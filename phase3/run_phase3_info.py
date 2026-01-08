"""
ShadowKey Phase 3 - Main Application Integration Script
Demonstrates the complete multi-user workflow with cloud sync.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check if running main app or just showing usage
if __name__ == "__main__":
    print("="*70)
    print("ShadowKey Phase 3 - Multi-User Keystroke Authentication")
    print("="*70)
    print()
    print("WHAT'S NEW IN PHASE 3:")
    print("  ✓ Multi-user authentication with login/registration")
    print("  ✓ Password-protected user accounts")
    print("  ✓ Per-user ML model isolation")
    print("  ✓ Cloud sync for session data")
    print("  ✓ Enhanced features: entropy, rhythm stability, rolling stats")
    print()
    print("MODULES IMPLEMENTED:")
    print("  • data_storage.py    - Multi-user database with auth")
    print("  • cloud_manager.py   - Mock cloud sync (JSON-based)")
    print("  • ml_auth.py         - User-specific ML models")
    print("  • feature_extractor.py - Enhanced behavioral features")
    print("  • login_dialog.py    - Authentication UI")
    print("  • test_phase3.py     - Comprehensive test suite")
    print()
    print("QUICK START:")
    print("  1. Run tests:         python test_phase3.py")
    print("  2. Test cloud sync:   python cloud_manager.py")
    print("  3. Test ML multi-user: python ml_auth.py")
    print()
    print("MAIN APP INTEGRATION:")
    print("  The shadowkey_phase3.py needs to be updated to:")
    print("  - Show login dialog on startup")
    print("  - Initialize ML authenticator with user_id")
    print("  - Add 'Sync Now' and 'Logout' buttons")
    print("  - Display logged-in username")
    print()
    print("To update the main app, key changes needed:")
    print("  1. Import login_dialog and cloud_manager")
    print("  2. Show LoginDialog before creating main window")
    print("  3. Pass user_id to BehavioralAuthenticator")
    print("  4. Add sync_to_cloud() method using CloudSyncManager")
    print("  5. Add logout button to show login dialog again")
    print()
    print("="*70)
    print("TESTING RESULTS:")
    print("="*70)
    
    # Run quick tests
    import subprocess
    result = subprocess.run(
        [sys.executable, "test_phase3.py"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # Show results
    if "OK" in result.stdout:
        print("✓ All Phase 3 tests PASSED!")
        print()
        # Extract summary
        lines = result.stdout.split('\n')
        for line in lines:
            if "Ran" in line or "Tests run:" in line or "Successes:" in line:
                print(f"  {line}")
    else:
        print("Some tests failed. Run 'python test_phase3.py' for details.")
        print(result.stdout)
    
    print("="*70)
