"""
ShadowKey Phase 4 - Voice Biometric Authentication
Machine learning model for voice-based user verification.
"""

import pickle
import numpy as np
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler

class VoiceAuthenticator:
    """
    Voice biometrics authenticator using One-Class SVM.
    """
    
    def __init__(self, 
                 model_dir: str = "models", 
                 user_id: int = None,
                 nu: float = 0.1, 
                 gamma: str = 'scale'):
        """
        Initialize voice authenticator.
        
        Args:
            model_dir: Directory to store models
            user_id: ID of the user
            nu: Anomaly fraction (similar to contamination)
            gamma: Kernel coefficient for RBF
        """
        self.model_dir = Path(model_dir)
        self.user_id = user_id
        self.nu = nu
        self.gamma = gamma
        self.logger = logging.getLogger(__name__)
        
        # Paths
        if user_id is not None:
            self.user_model_dir = self.model_dir / f"user_{user_id}"
            self.user_model_dir.mkdir(parents=True, exist_ok=True)
            self.model_path = self.user_model_dir / "voice_auth_model.pkl"
            self.scaler_path = self.user_model_dir / "voice_scaler.pkl"
        else:
            self.model_path = None
            self.scaler_path = None
        
        self.model: Optional[OneClassSVM] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained = False
        
    def train(self, features: List[np.ndarray], save_model: bool = True) -> Dict[str, Any]:
        """
        Train the voice model on provided features.
        
        Args:
            features: List of feature vectors (numpy arrays)
            save_model: Whether to save to disk immediately
            
        Returns:
            Dictionary with training stats
        """
        if not features:
            return {'status': 'error', 'message': 'No features provided'}
            
        X = np.array(features)
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train One-Class SVM
        self.model = OneClassSVM(kernel='rbf', nu=self.nu, gamma=self.gamma)
        self.model.fit(X_scaled)
        
        self.is_trained = True
        
        if save_model:
            self.save_model()
            
        return {
            'status': 'success',
            'n_samples': len(X),
            'n_features': X.shape[1],
            'user_id': self.user_id
        }
        
    def predict(self, feature_vector: np.ndarray) -> Tuple[bool, float]:
        """
        Verify a voice sample.
        
        Args:
            feature_vector: Feature vector of the sample
            
        Returns:
            Tuple (is_authorized, confidence_score)
            is_authorized: True if voice matches model
            confidence_score: 0.0 to 1.0 (approximate)
        """
        if not self.is_trained:
            self.logger.warning("Attempted prediction on untrained model")
            return False, 0.0
            
        # Scale input
        X = np.array([feature_vector])
        X_scaled = self.scaler.transform(X)
        
        # Predict
        # 1 for inlier, -1 for outlier
        pred = self.model.predict(X_scaled)[0]
        
        # Decision function distance
        # Positive = inlier, Negative = outlier
        dist = self.model.decision_function(X_scaled)[0]
        
        # Convert distance to a confidence-like score
        # Sigmoid-ish scaling
        confidence = 1 / (1 + np.exp(-dist * 2))
        
        is_authorized = (pred == 1)
        
        return is_authorized, float(confidence)

    def save_model(self) -> bool:
        """Save model and scaler to disk."""
        if not self.is_trained or not self.model_path:
            return False
            
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            return True
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
            return False

    def load_model(self) -> bool:
        """Load model and scaler from disk."""
        if not self.model_path or not self.model_path.exists():
            return False
            
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            self.is_trained = True
            return True
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False

if __name__ == "__main__":
    # Test
    auth = VoiceAuthenticator(user_id=999)
    
    # Synthetic data
    train_data = [np.random.rand(20) for _ in range(10)]
    auth.train(train_data)
    
    test_data = np.random.rand(20)
    auth, conf = auth.predict(test_data)
    print(f"Auth: {auth}, Conf: {conf:.2f}")
    
    auth.save_model()
    print("Model saved and tested.")
