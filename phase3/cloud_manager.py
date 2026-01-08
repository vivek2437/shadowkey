"""
ShadowKey Phase 3 - Cloud Sync Manager
Mock cloud storage implementation using local JSON files.
Simulates cloud sync for multi-user keystroke data.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class CloudSyncManager:
    """Mock cloud storage manager using local JSON files."""
    
    def __init__(self, storage_dir: str = "cloud_storage"):
        """
        Initialize cloud sync manager.
        
        Args:
            storage_dir: Directory to store mock cloud data
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_dir(self, user_id: int) -> Path:
        """
        Get storage directory for a specific user.
        
        Args:
            user_id: ID of user
            
        Returns:
            Path to user's cloud storage directory
        """
        user_dir = self.storage_dir / f"user_{user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def sync_up(self, user_id: int, session_data: Dict[str, Any]) -> bool:
        """
        Upload session data to mock cloud storage.
        
        Args:
            user_id: ID of user
            session_data: Complete session data including keystrokes, features, predictions
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            user_dir = self._get_user_dir(user_id)
            session_id = session_data.get('session', {}).get('session_id')
            
            if not session_id:
                return False
            
            # Create session file
            session_file = user_dir / f"session_{session_id}.json"
            
            # Add sync metadata
            session_data['sync_metadata'] = {
                'synced_at': datetime.now().isoformat(),
                'user_id': user_id,
                'sync_type': 'upload'
            }
            
            # Write to file
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Cloud sync up failed: {e}")
            return False
    
    def sync_down(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Download all cloud sessions for a user.
        
        Args:
            user_id: ID of user
            
        Returns:
            List of session data dictionaries
        """
        try:
            user_dir = self._get_user_dir(user_id)
            sessions = []
            
            # Read all session files for this user
            for session_file in user_dir.glob("session_*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                        sessions.append(session_data)
                except Exception as e:
                    print(f"Failed to read {session_file}: {e}")
            
            return sessions
            
        except Exception as e:
            print(f"Cloud sync down failed: {e}")
            return []
    
    def get_sync_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get cloud sync status for a user.
        
        Args:
            user_id: ID of user
            
        Returns:
            Dictionary with sync status information
        """
        try:
            user_dir = self._get_user_dir(user_id)
            session_files = list(user_dir.glob("session_*.json"))
            
            total_sessions = len(session_files)
            last_sync = None
            
            # Find most recent sync
            if session_files:
                latest_file = max(session_files, key=lambda p: p.stat().st_mtime)
                last_sync = datetime.fromtimestamp(
                    latest_file.stat().st_mtime
                ).isoformat()
            
            return {
                'user_id': user_id,
                'total_cloud_sessions': total_sessions,
                'last_sync': last_sync,
                'storage_path': str(user_dir),
                'status': 'healthy'
            }
            
        except Exception as e:
            return {
                'user_id': user_id,
                'status': 'error',
                'error': str(e)
            }
    
    def delete_session(self, user_id: int, session_id: int) -> bool:
        """
        Delete a session from cloud storage.
        
        Args:
            user_id: ID of user
            session_id: ID of session to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            user_dir = self._get_user_dir(user_id)
            session_file = user_dir / f"session_{session_id}.json"
            
            if session_file.exists():
                session_file.unlink()
                return True
            return False
            
        except Exception as e:
            print(f"Failed to delete cloud session: {e}")
            return False
    
    def get_session(self, user_id: int, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific session from cloud.
        
        Args:
            user_id: ID of user
            session_id: ID of session to retrieve
            
        Returns:
            Session data or None if not found
        """
        try:
            user_dir = self._get_user_dir(user_id)
            session_file = user_dir / f"session_{session_id}.json"
            
            if session_file.exists():
                with open(session_file, 'r') as f:
                    return json.load(f)
            return None
            
        except Exception as e:
            print(f"Failed to retrieve cloud session: {e}")
            return None


# Example usage and testing
if __name__ == "__main__":
    print("Testing Cloud Sync Manager")
    
    manager = CloudSyncManager("test_cloud_storage")
    
    # Test sync up
    test_session = {
        'session': {
            'session_id': 1,
            'user_id': 1,
            'start_time': datetime.now().isoformat(),
            'total_keys': 100
        },
        'keystrokes': [
            {'key': 'h', 'timestamp': 0.0},
            {'key': 'e', 'timestamp': 0.1}
        ],
        'features': {
            'avg_hold_time': 0.08,
            'typing_speed': 3.5
        }
    }
    
    print("\nSyncing session to cloud...")
    success = manager.sync_up(1, test_session)
    print(f"Sync up: {'Success' if success else 'Failed'}")
    
    print("\nGetting sync status...")
    status = manager.get_sync_status(1)
    print(f"Status: {status}")
    
    print("\nSyncing down all sessions...")
    sessions = manager.sync_down(1)
    print(f"Retrieved {len(sessions)} sessions")
    
    print("\nCloud Sync Manager test complete!")
