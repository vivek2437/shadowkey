"""
Data Storage Module for ShadowKey Phase 1

This module manages SQLite database operations for storing keystroke events,
sessions, and extracted features. Also provides JSON export functionality.
"""

import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
from keystroke_capture import KeystrokeEvent


class DataStorage:
    """
    Manages persistent storage of keystroke data and features using SQLite.
    
    Database schema:
    - sessions: Stores session metadata
    - keystrokes: Stores individual keystroke events
    - features: Stores extracted features for each session
    """
    
    def __init__(self, db_path: str = "shadowkey_data.db"):
        """
        Initialize database connection and create tables if needed.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.init_database()
        
    def init_database(self):
        """Create database tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                total_keys INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create keystrokes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keystrokes (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                timestamp REAL NOT NULL,
                event_type TEXT NOT NULL,
                key_code INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')
        
        # Create features table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS features (
                feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                feature_data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')
        
        self.conn.commit()
        
    def create_session(self, user_id: str, start_time: float) -> int:
        """
        Create a new typing session.
        
        Args:
            user_id: Identifier for the user
            start_time: Unix timestamp of session start
            
        Returns:
            Session ID of the newly created session
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (user_id, start_time)
            VALUES (?, ?)
        ''', (user_id, start_time))
        self.conn.commit()
        return cursor.lastrowid
        
    def update_session(self, session_id: int, end_time: float, total_keys: int):
        """
        Update session with end time and total key count.
        
        Args:
            session_id: ID of the session to update
            end_time: Unix timestamp of session end
            total_keys: Total number of keys typed in session
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE sessions
            SET end_time = ?, total_keys = ?
            WHERE session_id = ?
        ''', (end_time, total_keys, session_id))
        self.conn.commit()
        
    def store_keystrokes(self, session_id: int, events: List[KeystrokeEvent]):
        """
        Store keystroke events for a session.
        
        Args:
            session_id: ID of the session
            events: List of KeystrokeEvent objects to store
        """
        cursor = self.conn.cursor()
        
        for event in events:
            cursor.execute('''
                INSERT INTO keystrokes (session_id, key, timestamp, event_type, key_code)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, event.key, event.timestamp, event.event_type, event.key_code))
        
        self.conn.commit()
        
    def store_features(self, session_id: int, features: Dict):
        """
        Store extracted features for a session.
        
        Args:
            session_id: ID of the session
            features: Dictionary of extracted features
        """
        cursor = self.conn.cursor()
        
        # Convert features dict to JSON string
        features_json = json.dumps(features, indent=2)
        
        cursor.execute('''
            INSERT INTO features (session_id, feature_data)
            VALUES (?, ?)
        ''', (session_id, features_json))
        
        self.conn.commit()
        
    def get_session(self, session_id: int) -> Optional[Dict]:
        """
        Retrieve session data by ID.
        
        Args:
            session_id: ID of the session to retrieve
            
        Returns:
            Dictionary containing session data or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT session_id, user_id, start_time, end_time, total_keys, created_at
            FROM sessions
            WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'session_id': row[0],
                'user_id': row[1],
                'start_time': row[2],
                'end_time': row[3],
                'total_keys': row[4],
                'created_at': row[5]
            }
        return None
        
    def get_session_keystrokes(self, session_id: int) -> List[Dict]:
        """
        Retrieve all keystrokes for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of keystroke event dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT event_id, key, timestamp, event_type, key_code
            FROM keystrokes
            WHERE session_id = ?
            ORDER BY timestamp
        ''', (session_id,))
        
        keystrokes = []
        for row in cursor.fetchall():
            keystrokes.append({
                'event_id': row[0],
                'key': row[1],
                'timestamp': row[2],
                'event_type': row[3],
                'key_code': row[4]
            })
        
        return keystrokes
        
    def get_session_features(self, session_id: int) -> Optional[Dict]:
        """
        Retrieve extracted features for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dictionary of features or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT feature_data
            FROM features
            WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None
        
    def export_session_to_json(self, session_id: int, output_file: str):
        """
        Export complete session data to JSON file.
        
        Args:
            session_id: ID of the session to export
            output_file: Path to output JSON file
        """
        # Get session metadata
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get keystrokes
        keystrokes = self.get_session_keystrokes(session_id)
        
        # Get features
        features = self.get_session_features(session_id)
        
        # Combine into export structure
        export_data = {
            'session_metadata': {
                'session_id': session['session_id'],
                'user_id': session['user_id'],
                'start_time': session['start_time'],
                'start_time_readable': datetime.fromtimestamp(session['start_time']).isoformat(),
                'end_time': session['end_time'],
                'end_time_readable': datetime.fromtimestamp(session['end_time']).isoformat() if session['end_time'] else None,
                'total_keys': session['total_keys'],
                'created_at': session['created_at']
            },
            'keystrokes': keystrokes,
            'features': features
        }
        
        # Write to JSON file
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
            
    def get_all_sessions(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        Get all sessions, optionally filtered by user ID.
        
        Args:
            user_id: Optional user ID to filter sessions
            
        Returns:
            List of session dictionaries
        """
        cursor = self.conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT session_id, user_id, start_time, end_time, total_keys, created_at
                FROM sessions
                WHERE user_id = ?
                ORDER BY start_time DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT session_id, user_id, start_time, end_time, total_keys, created_at
                FROM sessions
                ORDER BY start_time DESC
            ''')
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row[0],
                'user_id': row[1],
                'start_time': row[2],
                'end_time': row[3],
                'total_keys': row[4],
                'created_at': row[5]
            })
        
        return sessions
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
