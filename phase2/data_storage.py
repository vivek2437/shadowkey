"""
ShadowKey Phase 2 - Data Storage Module
Handles SQLite database operations for sessions, keystrokes, features, and ML predictions.
"""

import sqlite3
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


class DataStorage:
    """SQLite-based storage manager for keystroke data and ML predictions."""
    
    def __init__(self, db_path: str = "shadowkey_data.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.initialize_database()
    
    def initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                total_keys INTEGER DEFAULT 0,
                typing_speed REAL,
                error_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Keystrokes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keystrokes (
                keystroke_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Features table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS features (
                feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                feature_type TEXT NOT NULL,
                feature_value REAL NOT NULL,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # ML predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_predictions (
                prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                is_anomaly INTEGER NOT NULL,
                confidence_score REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        self.conn.commit()
    
    def create_user(self, username: str) -> int:
        """
        Create a new user or get existing user ID.
        
        Args:
            username: Username to create
            
        Returns:
            user_id of created or existing user
        """
        cursor = self.conn.cursor()
        
        # Try to get existing user
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new user
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        self.conn.commit()
        return cursor.lastrowid
    
    def create_session(self, user_id: int) -> int:
        """
        Start a new typing session.
        
        Args:
            user_id: ID of the user
            
        Returns:
            session_id of the newly created session
        """
        cursor = self.conn.cursor()
        start_time = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO sessions (user_id, start_time)
            VALUES (?, ?)
        """, (user_id, start_time))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def save_keystroke(self, session_id: int, key: str, event_type: str, timestamp: float) -> None:
        """
        Record a single keystroke event.
        
        Args:
            session_id: ID of current session
            key: Key that was pressed
            event_type: 'down' or 'up'
            timestamp: Event timestamp with microsecond precision
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO keystrokes (session_id, key, event_type, timestamp)
            VALUES (?, ?, ?, ?)
        """, (session_id, key, event_type, timestamp))
        self.conn.commit()
    
    def save_features(self, session_id: int, features_dict: Dict[str, float]) -> None:
        """
        Batch save extracted features for a session.
        
        Args:
            session_id: ID of current session
            features_dict: Dictionary of feature_name: value pairs
        """
        cursor = self.conn.cursor()
        
        for feature_type, feature_value in features_dict.items():
            cursor.execute("""
                INSERT INTO features (session_id, feature_type, feature_value)
                VALUES (?, ?, ?)
            """, (session_id, feature_type, feature_value))
        
        self.conn.commit()
    
    def save_prediction(self, session_id: int, timestamp: float, is_anomaly: bool, confidence: float) -> None:
        """
        Store an ML prediction result.
        
        Args:
            session_id: ID of current session
            timestamp: When prediction was made
            is_anomaly: Whether typing pattern was flagged as anomalous
            confidence: Confidence score (0-1)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO ml_predictions (session_id, timestamp, is_anomaly, confidence_score)
            VALUES (?, ?, ?, ?)
        """, (session_id, timestamp, int(is_anomaly), confidence))
        self.conn.commit()
    
    def end_session(self, session_id: int, total_keys: int, typing_speed: float, error_count: int) -> None:
        """
        Mark session as complete and save summary statistics.
        
        Args:
            session_id: ID of session to end
            total_keys: Total keystrokes in session
            typing_speed: Average typing speed (CPS)
            error_count: Total errors (backspace/delete count)
        """
        cursor = self.conn.cursor()
        end_time = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE sessions
            SET end_time = ?, total_keys = ?, typing_speed = ?, error_count = ?
            WHERE session_id = ?
        """, (end_time, total_keys, typing_speed, error_count, session_id))
        
        self.conn.commit()
    
    def get_user_sessions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve historical sessions for a user.
        
        Args:
            user_id: ID of user
            limit: Maximum number of sessions to retrieve
            
        Returns:
            List of session dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sessions
            WHERE user_id = ?
            ORDER BY start_time DESC
            LIMIT ?
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_session_keystrokes(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Get all keystrokes for a specific session.
        
        Args:
            session_id: ID of session
            
        Returns:
            List of keystroke dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM keystrokes
            WHERE session_id = ?
            ORDER BY timestamp
        """, (session_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_session_features(self, session_id: int) -> Dict[str, float]:
        """
        Get all features for a specific session.
        
        Args:
            session_id: ID of session
            
        Returns:
            Dictionary of feature_type: feature_value pairs
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT feature_type, feature_value FROM features
            WHERE session_id = ?
        """, (session_id,))
        
        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}
    
    def export_session_json(self, session_id: int, output_path: str) -> None:
        """
        Export session data to JSON format.
        
        Args:
            session_id: ID of session to export
            output_path: Path to output JSON file
        """
        # Get session info
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        session = dict(cursor.fetchone())
        
        # Get keystrokes
        keystrokes = self.get_session_keystrokes(session_id)
        
        # Get features
        features = self.get_session_features(session_id)
        
        # Get ML predictions
        cursor.execute("""
            SELECT * FROM ml_predictions
            WHERE session_id = ?
            ORDER BY timestamp
        """, (session_id,))
        predictions = [dict(row) for row in cursor.fetchall()]
        
        # Combine into export structure
        export_data = {
            "session": session,
            "keystrokes": keystrokes,
            "features": features,
            "ml_predictions": predictions,
            "export_timestamp": datetime.now().isoformat()
        }
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def export_session_csv(self, session_id: int, output_path: str) -> None:
        """
        Export session keystrokes to CSV format.
        
        Args:
            session_id: ID of session to export
            output_path: Path to output CSV file
        """
        keystrokes = self.get_session_keystrokes(session_id)
        
        if not keystrokes:
            return
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write CSV
        with open(output_path, 'w', newline='') as f:
            fieldnames = keystrokes[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(keystrokes)
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
