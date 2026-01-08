"""
ShadowKey Phase 3 - Machine Learning Authentication Module
Behavioral authentication with multi-user support and multiple model types.
Supports Isolation Forest and extensions for Autoencoder models.
"""

import pickle
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')


class BehavioralAuthenticator:
    """
    ML-based behavioral authentication using unsupervised anomaly detection.
    Supports multi-user model isolation with per-user directories.
    """
    
    def __init__(self, 
                 model_dir: str = "models",
                 user_id: int = None,
                 model_type: str = 'isolation_forest',
                 contamination: float = 0.05):
        """
        Initialize authenticator with model parameters.
        
        Args:
            model_dir: Base directory for model storage
            user_id: User ID for model isolation (None creates default path)
            model_type: Type of model ('isolation_forest' or 'autoencoder')
            contamination: Expected proportion of anomalies (0.01-0.5)
        """
        self.model_dir = Path(model_dir)
        self.user_id = user_id
        self.model_type = model_type
        self.contamination = contamination
        
        # Initialize paths based on user_id
        if user_id is not None:
            self.user_model_dir = self.model_dir / f"user_{user_id}"
            self.user_model_dir.mkdir(parents=True, exist_ok=True)
            self.model_path = self.user_model_dir / "behavioral_auth.pkl"
            self.scaler_path = self.user_model_dir / "feature_scaler.pkl"
        else:
            # Default paths for backward compatibility
            self.model_path = self.model_dir / "behavioral_auth.pkl"
            self.scaler_path = self.model_dir / "feature_scaler.pkl"
            self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Model components
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained = False
        self.training_samples = 0
    
    def train(self, training_features: List[List[float]], save_model: bool = True) -> Dict[str, Any]:
        """
        Train model on legitimate user typing patterns.
        
        Args:
            training_features: List of feature vectors from legitimate sessions
            save_model: Whether to save the trained model to disk
            
        Returns:
            Dictionary with training statistics
        """
        if not training_features:
            return {'error': 'No training data provided'}
        
        # Convert to numpy array
        X = np.array(training_features)
        self.training_samples = len(X)
        
        # Initialize and fit scaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Initialize model based on type
        if self.model_type == 'isolation_forest':
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100
            )
        else:
            # Placeholder for future model types
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100
            )
        
        # Train model
        self.model.fit(X_scaled)
        self.is_trained = True
        
        # Save model if requested
        if save_model:
            self.save_model()
        
        return {
            'status': 'success',
            'model_type': self.model_type,
            'training_samples': self.training_samples,
            'features_per_sample': X.shape[1],
            'contamination': self.contamination,
            'user_id': self.user_id
        }
    
    def predict_live(self, current_features: List[float]) -> Tuple[bool, float]:
        """
        Predict if current typing pattern is anomalous.
        
        Args:
            current_features: Feature vector from current session
            
        Returns:
            Tuple of (is_anomaly, confidence_score)
            - is_anomaly: True if pattern is flagged as anomalous
            - confidence_score: 0-1, higher = more confident it's legitimate
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Prepare features
        X = np.array([current_features])
        try:
            X_scaled = self.scaler.transform(X)
            prediction = self.model.predict(X_scaled)[0]
            anomaly_score = self.model.score_samples(X_scaled)[0]
        except ValueError as e:
            if "expect" in str(e) and "features" in str(e):
                print(f"Feature mismatch detected: {e}. Model requires retraining.")
                self.is_trained = False
                return False, 0.0
            raise e
        
        # Convert to boolean and confidence
        is_anomaly = (prediction == -1)
        confidence = self._score_to_confidence(anomaly_score)
        
        return is_anomaly, confidence
    
    def _score_to_confidence(self, score: float) -> float:
        """
        Convert anomaly score to confidence percentage.
        
        Args:
            score: Raw anomaly score from model
            
        Returns:
            Confidence score between 0 and 1
        """
        # Clamp score to reasonable range
        score = np.clip(score, -0.5, 0.5)
        
        # Normalize to 0-1 (0 = definitely anomaly, 1 = definitely normal)
        confidence = (score + 0.5) / 1.0
        
        return float(confidence)
    
    def retrain_incremental(self, new_session_features: List[float], 
                           all_sessions: List[List[float]]) -> Dict[str, Any]:
        """
        Retrain model with new legitimate session added.
        
        Args:
            new_session_features: Features from new legitimate session
            all_sessions: All legitimate sessions including new one
            
        Returns:
            Training statistics
        """
        return self.train(all_sessions)
    
    def save_model(self) -> None:
        """Save trained model and scaler to disk."""
        if not self.is_trained:
            print("Warning: No trained model to save")
            return
        
        # Ensure directory exists
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save scaler
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        user_str = f" for user {self.user_id}" if self.user_id else ""
        print(f"Model saved{user_str}: {self.model_path}")
    
    def load_model(self) -> bool:
        """
        Load trained model and scaler from disk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load model
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Load scaler
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            self.is_trained = True
            
            user_str = f" for user {self.user_id}" if self.user_id else ""
            print(f"Model loaded{user_str}: {self.model_path}")
            return True
        
        except FileNotFoundError:
            print("Model files not found")
            return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the trained model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'is_trained': self.is_trained,
            'user_id': self.user_id,
            'model_type': self.model_type,
            'training_samples': self.training_samples,
            'contamination': self.contamination,
            'model_path': str(self.model_path),
            'scaler_path': str(self.scaler_path),
            'model_exists': self.model_path.exists() if self.model_path else False,
            'scaler_exists': self.scaler_path.exists() if self.scaler_path else False
        }
    
    def set_user(self, user_id: int) -> None:
        """
        Switch to a different user's model context.
        
        Args:
            user_id: ID of user to switch to
        """
        self.user_id = user_id
        self.user_model_dir = self.model_dir / f"user_{user_id}"
        self.user_model_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.user_model_dir / "behavioral_auth.pkl"
        self.scaler_path = self.user_model_dir / "feature_scaler.pkl"
        
        # Reset trained state when switching users
        self.is_trained = False
        self.model = None
        self.scaler = None
        self.training_samples = 0


# Example usage
if __name__ == "__main__":
    print("Testing Multi-User Authentication")
    
    np.random.seed(42)
    
    # Simulate training data for User 1
    user1_sessions = []
    for i in range(5):
        features = list(np.random.normal(loc=[0.05, 0.04] + [0.1] * 18, scale=0.01, size=20))
        user1_sessions.append(features)
    
    # Train model for User 1
    auth = BehavioralAuthenticator(user_id=1)
    stats = auth.train(user1_sessions)
    print(f"\nUser 1 training: {stats}")
    
    # Test on User 1-like pattern
    test_u1 = list(np.random.normal(loc=[0.05, 0.04] + [0.1] * 18, scale=0.01, size=20))
    is_anomaly, confidence = auth.predict_live(test_u1)
    print(f"User 1 pattern: anomaly={is_anomaly}, confidence={confidence:.2f}")
    
    # Simulate User 2 (different pattern)
    auth.set_user(2)
    user2_sessions = []
    for i in range(5):
        features = list(np.random.normal(loc=[0.15, 0.14] + [0.2] * 18, scale=0.02, size=20))
        user2_sessions.append(features)
    
    stats = auth.train(user2_sessions)
    print(f"\nUser 2 training: {stats}")
    
    # Test User 2 pattern on User 2's model (should match)
    test_u2 = list(np.random.normal(loc=[0.15, 0.14] + [0.2] * 18, scale=0.02, size=20))
    is_anomaly, confidence = auth.predict_live(test_u2)
    print(f"User 2 pattern on User 2 model: anomaly={is_anomaly}, confidence={confidence:.2f}")
    
    # Switch back to User 1 and load their model
    auth.set_user(1)
    auth.load_model()
    
    # Test User 2 pattern on User 1's model (should NOT match)
    is_anomaly, confidence = auth.predict_live(test_u2)
    print(f"User 2 pattern on User 1 model: anomaly={is_anomaly}, confidence={confidence:.2f}")
    
    print("\nMulti-user authentication test complete!")
