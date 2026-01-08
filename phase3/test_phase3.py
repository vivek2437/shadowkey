"""
ShadowKey Phase 3 - Test Suite
Comprehensive tests for multi-user authentication, cloud sync, and enhanced ML features.
"""

import unittest
import os
import json
from pathlib import Path
import tempfile
import shutil

# Import Phase 3 modules
from data_storage import DataStorage
from cloud_manager import CloudSyncManager
from ml_auth import BehavioralAuthenticator
from feature_extractor import FeatureExtractor, KeyEvent


class TestPhase3Database(unittest.TestCase):
    """Test multi-user database schema and authentication."""
    
    def setUp(self):
        """Create temporary database for testing."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db = DataStorage(self.test_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        self.db.close()
        os.unlink(self.test_db.name)
    
    def test_user_creation_with_password(self):
        """Test creating users with password hashing."""
        user_id = self.db.create_user("alice", "password123")
        self.assertIsNotNone(user_id)
        self.assertGreater(user_id, 0)
    
    def test_user_authentication(self):
        """Test user authentication with correct/incorrect passwords."""
        # Create user
        self.db.create_user("bob", "secret456")
        
        # Test correct password
        user_id = self.db.authenticate_user("bob", "secret456")
        self.assertIsNotNone(user_id)
        
        # Test incorrect password
        user_id = self.db.authenticate_user("bob", "wrongpassword")
        self.assertIsNone(user_id)
    
    def test_session_sync_status(self):
        """Test session sync status tracking."""
        user_id = self.db.create_user("charlie", "pass789")
        session_id = self.db.create_session(user_id)
        
        # End session
        self.db.end_session(session_id, 100, 5.0, 2)
        
        # Check pending sync
        pending = self.db.get_pending_sync_sessions(user_id)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['sync_status'], 'pending')
        
        # Mark as synced
        self.db.mark_session_synced(session_id)
        pending = self.db.get_pending_sync_sessions(user_id)
        self.assertEqual(len(pending), 0)


class TestCloudSync(unittest.TestCase):
    """Test cloud synchronization manager."""
    
    def setUp(self):
        """Create temporary cloud storage directory."""
        self.test_dir = tempfile.mkdtemp()
        self.cloud_manager = CloudSyncManager(self.test_dir)
    
    def tearDown(self):
        """Clean up test cloud storage."""
        shutil.rmtree(self.test_dir)
    
    def test_sync_up(self):
        """Test uploading session to cloud."""
        session_data = {
            'session': {
                'session_id': 1,
                'user_id': 1,
                'total_keys': 100
            },
            'keystrokes': [
                {'key': 'a', 'timestamp': 0.0},
                {'key': 'b', 'timestamp': 0.1}
            ],
            'features': {
                'typing_speed': 5.0
            }
        }
        
        success = self.cloud_manager.sync_up(1, session_data)
        self.assertTrue(success)
        
        # Verify file exists
        user_dir = Path(self.test_dir) / "user_1"
        self.assertTrue(user_dir.exists())
        
        session_file = user_dir / "session_1.json"
        self.assertTrue(session_file.exists())
    
    def test_sync_down(self):
        """Test downloading sessions from cloud."""
        # Upload test session
        session_data = {
            'session': {'session_id': 2, 'user_id': 2},
            'keystrokes': []
        }
        self.cloud_manager.sync_up(2, session_data)
        
        # Download
        sessions = self.cloud_manager.sync_down(2)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]['session']['session_id'], 2)
    
    def test_get_sync_status(self):
        """Test getting cloud sync status."""
        # Upload session
        session_data = {'session': {'session_id': 3, 'user_id': 3}, 'keystrokes': []}
        self.cloud_manager.sync_up(3, session_data)
        
        # Check status
        status = self.cloud_manager.get_sync_status(3)
        self.assertEqual(status['total_cloud_sessions'], 1)
        self.assertIsNotNone(status['last_sync'])


class TestEnhancedFeatures(unittest.TestCase):
    """Test enhanced feature extraction (entropy, rhythm stability)."""
    
    def setUp(self):
        """Initialize feature extractor."""
        self.extractor = FeatureExtractor()
    
    def test_sequence_entropy(self):
        """Test Shannon entropy calculation."""
        # Create varied keystroke sequence
        events = [
            KeyEvent('a', 'down', 0.0),
            KeyEvent('a', 'up', 0.05),
            KeyEvent('b', 'down', 0.1),
            KeyEvent('b', 'up', 0.15),
            KeyEvent('c', 'down', 0.2),
            KeyEvent('c', 'up', 0.25),
        ]
        
        self.extractor.process_events(events)
        entropy = self.extractor.get_sequence_entropy()
        
        # Should have some entropy for varied sequence
        self.assertGreater(entropy, 0)
    
    def test_rhythm_stability(self):
        """Test rhythm stability calculation."""
        # Create consistent typing rhythm
        events = []
        for i in range(20):
            events.append(KeyEvent('a', 'down', i * 0.1))
            events.append(KeyEvent('a', 'up', i * 0.1 + 0.05))
        
        self.extractor.process_events(events)
        rhythm = self.extractor.get_rhythm_stability()
        
        # Should have low variance (stable rhythm)
        self.assertIsInstance(rhythm, float)
        self.assertGreaterEqual(rhythm, 0)
    
    def test_rolling_speed_stats(self):
        """Test rolling speed statistics."""
        events = []
        for i in range(30):
            events.append(KeyEvent('a', 'down', i * 0.1))
            events.append(KeyEvent('a', 'up', i * 0.1 + 0.05))
        
        self.extractor.process_events(events)
        stats = self.extractor.get_rolling_speed_stats()
        
        self.assertIn('rolling_mean', stats)
        self.assertIn('rolling_std', stats)
        self.assertIsInstance(stats['rolling_mean'], float)


class TestMultiUserML(unittest.TestCase):
    """Test multi-user ML model isolation."""
    
    def setUp(self):
        """Create temporary model directory."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test models."""
        shutil.rmtree(self.test_dir)
    
    def test_user_specific_model_paths(self):
        """Test that different users have separate model directories."""
        auth1 = BehavioralAuthenticator(model_dir=self.test_dir, user_id=1)
        auth2 = BehavioralAuthenticator(model_dir=self.test_dir, user_id=2)
        
        self.assertNotEqual(str(auth1.model_path), str(auth2.model_path))
        self.assertTrue('user_1' in str(auth1.model_path))
        self.assertTrue('user_2' in str(auth2.model_path))
    
    def test_set_user_switches_context(self):
        """Test switching user context updates model paths."""
        auth = BehavioralAuthenticator(model_dir=self.test_dir, user_id=1)
        original_path = str(auth.model_path)
        
        auth.set_user(2)
        new_path = str(auth.model_path)
        
        self.assertNotEqual(original_path, new_path)
        self.assertTrue('user_2' in new_path)


def run_all_tests():
    """Run full test suite."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPhase3Database))
    suite.addTests(loader.loadTestsFromTestCase(TestCloudSync))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiUserML))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
