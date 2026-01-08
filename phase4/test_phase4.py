"""
ShadowKey Phase 4 - Automated Verification Script
Tests Voice Pipeline and Fusion Logic.
"""

import unittest
import numpy as np
import os
import shutil
import sys
from pathlib import Path

# Add local directory to path
sys.path.append(os.getcwd())

# Import modules to test
from voice_features import VoiceFeatureExtractor
from voice_auth import VoiceAuthenticator
from fusion_engine import FusionEngine

class TestShadowKeyPhase4(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("\n=== Starting Phase 4 Verification ===")
        cls.test_model_dir = "test_models_phase4"
        if os.path.exists(cls.test_model_dir):
            shutil.rmtree(cls.test_model_dir)
        os.makedirs(cls.test_model_dir)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_model_dir):
            shutil.rmtree(cls.test_model_dir)
        print("\n=== verification Complete ===")

    def test_01_feature_extraction(self):
        print("\n[Test] Voice Feature Extraction")
        extractor = VoiceFeatureExtractor(sample_rate=22050)
        
        # 1. Sine wave (Pure tone)
        t = np.linspace(0, 2.0, int(22050*2))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t) # 440Hz
        
        features = extractor.extract_features(audio.astype(np.float32))
        
        self.assertIsNotNone(features, "Features should not be None")
        self.assertTrue(len(features) > 10, "Should have multiple features")
        print(f"  > Extracted {len(features)} features from synthetic audio")
        
        # 2. Silence/Noise
        silence = np.zeros(22050*2, dtype=np.float32)
        feats_silence = extractor.extract_features(silence)
        # It might return None due to trimming or low energy
        if feats_silence is None:
            print("  > Silence correctly handled (ignored)")
        else:
            print("  > Warning: Silence produced features")

    def test_02_voice_auth_model(self):
        print("\n[Test] Voice Auth Model (OneClassSVM)")
        auth = VoiceAuthenticator(model_dir=self.test_model_dir, user_id=123)
        
        # Generate synthetic user data (Cluster around 0.5)
        # 50 samples, 20 features each (Increased from 10)
        train_data = []
        for _ in range(50):
            sample = np.random.normal(loc=0.5, scale=0.05, size=20)
            train_data.append(sample)
            
        # Train
        res = auth.train(train_data)
        self.assertEqual(res['status'], 'success')
        self.assertTrue(auth.is_trained)
        print(f"  > Trained on {res['n_samples']} samples")
        
        # Predict Valid
        valid_sample = np.random.normal(loc=0.5, scale=0.05, size=20)
        is_auth, conf = auth.predict(valid_sample)
        print(f"  > Valid Sample: Auth={is_auth}, Conf={conf:.2f}")
        # OneClassSVM can be finicky with small data or random seeds, but with 50 it should be better
        # We assert true, but if it fails comfortably (e.g. 0.49), we might need to tune 'nu'
        self.assertTrue(is_auth, f"Should accept valid sample (Conf: {conf:.2f})")
        
        # Predict Anomaly
        # Make anomaly very distinct (loc=5.0) for this test
        anomaly_sample = np.random.normal(loc=5.0, scale=0.1, size=20) 
        is_auth, conf = auth.predict(anomaly_sample)
        print(f"  > Anomaly Sample: Auth={is_auth}, Conf={conf:.2f}")
        self.assertFalse(is_auth, "Should reject anomaly")
        
        # Save/Load
        auth.save_model()
        
        auth2 = VoiceAuthenticator(model_dir=self.test_model_dir, user_id=123)
        loaded = auth2.load_model()
        self.assertTrue(loaded, "Model should load")
        
        is_auth, _ = auth2.predict(valid_sample)
        self.assertTrue(is_auth, "Loaded model should work")

    def test_03_fusion_logic(self):
        print("\n[Test] Fusion Engine")
        fusion = FusionEngine() 
        # config defaults: Weights(K=0.6, V=0.4), Thresholds(L=0.3, H=0.75)
        # But we rely on default class init values if file missing, let's force set for test
        fusion.weights = {'keystroke': 0.6, 'voice': 0.4}
        fusion.thresholds = {'low': 0.3, 'high': 0.75}

        # Case 1: High Confidence Both (Low Risk)
        # Conf=0.9 -> Risk=0.1
        risk = fusion.calculate_risk(0.9, 0.9)
        # Risk = 0.1*0.6 + 0.1*0.4 = 0.1
        self.assertAlmostEqual(risk, 0.1, delta=0.01)
        level = fusion.decide_auth_level(risk)
        self.assertEqual(level, FusionEngine.RISK_LOW)
        print(f"  > High Conf (0.9, 0.9) -> Risk {risk:.2f} (LOW)")
        
        # Case 2: Low Confidence Keystroke, High Voice
        # KS Conf=0.2 (Risk 0.8), V Conf=0.9 (Risk 0.1)
        # Risk = 0.8*0.6 + 0.1*0.4 = 0.48 + 0.04 = 0.52
        risk = fusion.calculate_risk(0.2, 0.9)
        self.assertAlmostEqual(risk, 0.52, delta=0.01)
        level = fusion.decide_auth_level(risk)
        self.assertEqual(level, FusionEngine.RISK_MEDIUM) # 0.3 < 0.52 < 0.75
        print(f"  > Mixed Conf (0.2, 0.9) -> Risk {risk:.2f} (MED - Verify)")
        
        # Case 3: Low Confidence Both
        # Conf=0.1 -> Risk=0.9
        risk = fusion.calculate_risk(0.1, 0.1)
        # Risk = 0.9
        level = fusion.decide_auth_level(risk)
        self.assertEqual(level, FusionEngine.RISK_HIGH)
        print(f"  > Low Conf (0.1, 0.1) -> Risk {risk:.2f} (HIGH)")

if __name__ == '__main__':
    unittest.main()
