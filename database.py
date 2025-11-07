#!/usr/bin/env python3
"""
Database module for Tyson Agent
Handles conversation persistence with MariaDB
"""
import mysql.connector
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self):
        """Initialize database connection with environment variables"""
        self.config = {
            'host': os.getenv('DB_HOST', 'llm_tyson'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'database': os.getenv('DB_NAME', 'llm'),
            'user': os.getenv('DB_USER', 'mariadb'),
            'password': os.getenv('DB_PASSWORD', ''),
            'autocommit': True
        }
    
    def get_connection(self):
        """Get a database connection"""
        try:
            return mysql.connector.connect(**self.config)
        except mysql.connector.Error as err:
            print(f"Database connection error: {err}")
            raise
    
    def init_tables(self):
        """Initialize database tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session (session_id),
                    INDEX idx_timestamp (timestamp)
                )
            ''')
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id VARCHAR(255) PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    metadata JSON
                )
            ''')
            
            print("✓ Database tables initialized")
            
        except mysql.connector.Error as err:
            print(f"Error creating tables: {err}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def save_message(self, session_id: str, role: str, content: str):
        """Save a message to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO conversations (session_id, role, content) VALUES (%s, %s, %s)",
                (session_id, role, content)
            )
            
            # Update or create session
            cursor.execute(
                "INSERT INTO sessions (session_id) VALUES (%s) ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP",
                (session_id,)
            )
            
        except mysql.connector.Error as err:
            print(f"Error saving message: {err}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for a session"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute(
                """SELECT role, content, timestamp 
                   FROM conversations 
                   WHERE session_id = %s 
                   ORDER BY timestamp ASC 
                   LIMIT %s""",
                (session_id, limit)
            )
            
            results = cursor.fetchall()
            
            # Convert timestamp to string for JSON serialization
            for row in results:
                if row['timestamp']:
                    row['timestamp'] = row['timestamp'].isoformat()
            
            return results
            
        except mysql.connector.Error as err:
            print(f"Error fetching history: {err}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def clear_history(self, session_id: str):
        """Clear conversation history for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM conversations WHERE session_id = %s",
                (session_id,)
            )
            print(f"✓ Cleared history for session {session_id}")
            
        except mysql.connector.Error as err:
            print(f"Error clearing history: {err}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_all_sessions(self, limit: int = 100) -> List[Dict]:
        """Get all sessions"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute(
                """SELECT session_id, created_at, updated_at, 
                   (SELECT COUNT(*) FROM conversations WHERE session_id = s.session_id) as message_count
                   FROM sessions s
                   ORDER BY updated_at DESC
                   LIMIT %s""",
                (limit,)
            )
            
            results = cursor.fetchall()
            
            # Convert timestamps
            for row in results:
                if row['created_at']:
                    row['created_at'] = row['created_at'].isoformat()
                if row['updated_at']:
                    row['updated_at'] = row['updated_at'].isoformat()
            
            return results
            
        except mysql.connector.Error as err:
            print(f"Error fetching sessions: {err}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def delete_session(self, session_id: str):
        """Delete a session and all its messages"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM conversations WHERE session_id = %s", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
            print(f"✓ Deleted session {session_id}")
            
        except mysql.connector.Error as err:
            print(f"Error deleting session: {err}")
            raise
        finally:
            cursor.close()
            conn.close()
