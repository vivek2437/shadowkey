"""
ShadowKey Phase 2 - Quick Test Script
Tests individual modules to verify they can be imported and initialized.
"""

def test_data_storage():
    """Test database storage module."""
    print("Testing data_storage.py...")
    try:
        from data_storage import DataStorage
        db = DataStorage('test_shadowkey.db')
        user_id = db.create_user('test_user')
        session_id = db.create_session(user_id)
        print(f"  ✓ Created user {user_id} and session {session_id}")
        db.close()
        print("  ✓ data_storage.py OK")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_system_capture():
    """Test system capture module."""
    print("\nTesting system_capture.py...")
    try:
        from system_capture import SystemCaptureManager, KeystrokeEvent
        manager = SystemCaptureManager()
        print("  ✓ SystemCaptureManager initialized")
        print("  ✓ system_capture.py OK")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_feature_extractor():
    """Test feature extraction module."""
    print("\nTesting feature_extractor.py...")
    try:
        from feature_extractor import FeatureExtractor, KeyEvent
        extractor = FeatureExtractor()
        
        # Simulate some events
        events = [
            KeyEvent('a', 'down', 0.0),
            KeyEvent('a', 'up', 0.05),
            KeyEvent('b', 'down', 0.1),
            KeyEvent('b', 'up', 0.15),
        ]
        extractor.process_events(events)
        summary = extractor.get_feature_summary()
        
        print(f"  ✓ Processed {len(events)} events")
        print(f"  ✓ Extracted features: {summary['total_keys']} keys")
        print("  ✓ feature_extractor.py OK")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_ml_auth():
    """Test ML authentication module."""
    print("\nTesting ml_auth.py...")
    try:
        from ml_auth import BehavioralAuthenticator
        import numpy as np
        
        auth = BehavioralAuthenticator(
            model_path='test_model.pkl',
            scaler_path='test_scaler.pkl'
        )
        
        # Create dummy training data
        training_data = []
        for i in range(5):
            features = list(np.random.normal(0.1, 0.01, 21))
            training_data.append(features)
        
        # Train
        stats = auth.train(training_data, save_model=False)
        print(f"  ✓ Trained on {stats['n_sessions']} sessions")
        
        # Test prediction
        test_features = list(np.random.normal(0.1, 0.01, 21))
        is_anomaly, confidence = auth.predict_live(test_features)
        print(f"  ✓ Prediction: anomaly={is_anomaly}, confidence={confidence:.2f}")
        print("  ✓ ml_auth.py OK")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_visualization():
    """Test visualization module (import only)."""
    print("\nTesting visualization.py...")
    try:
        # Only test import since Tkinter requires GUI
        from visualization import LiveVisualizer
        print("  ✓ LiveVisualizer imported successfully")
        print("  ⚠ Full visualization test requires GUI (run main app)")
        print("  ✓ visualization.py OK")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_config():
    """Test configuration file loading."""
    print("\nTesting config_phase2.json...")
    try:
        import json
        with open('config_phase2.json', 'r') as f:
            config = json.load(f)
        
        print(f"  ✓ Loaded config with {len(config)} sections")
        print(f"  ✓ ML contamination: {config['ml']['contamination']}")
        print("  ✓ config_phase2.json OK")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("ShadowKey Phase 2 - Module Tests")
    print("="*60)
    
    results = {
        'config': test_config(),
        'data_storage': test_data_storage(),
        'system_capture': test_system_capture(),
        'feature_extractor': test_feature_extractor(),
        'ml_auth': test_ml_auth(),
        'visualization': test_visualization(),
    }
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for module, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{module:20s}: {status}")
    
    print("-"*60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All modules working correctly!")
        print("✓ Ready to run: python shadowkey_phase2.py")
    else:
        print("\n⚠ Some modules failed - check error messages above")
    
    print("="*60)


if __name__ == "__main__":
    main()
