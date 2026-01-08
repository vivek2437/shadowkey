"""
ShadowKey Phase 2 - Machine Learning Authentication Module
Behavioral authentication using Isolation Forest for anomaly detection.
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
    Detects when typing patterns deviate from learned legitimate user behavior.
    """
    
    def __init__(self, model_path: str = "models/behavioral_auth.pkl", 
                 scaler_path: str = "models/feature_scaler.pkl",
                 contamination: float = 0.05):
        """
        Initialize authenticator with model parameters.
        
        Args:
            model_path: Path to save/load trained model
            scaler_path: Path to save/load feature scaler
            contamination: Expected proportion of anomalies (0.01-0.5)
        """
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.contamination = contamination
        
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained: bool = False
        self.feature_dim: Optional[int] = None
        
        # Ensure model directory exists
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    
    def train(self, training_features: List[List[float]], save_model: bool = True) -> Dict[str, Any]:
        """
        Train Isolation Forest on legitimate user typing patterns.
        
        Args:
            training_features: List of feature vectors from legitimate sessions
            save_model: Whether to save the trained model to disk
            
        Returns:
            Dictionary with training statistics
        """
        if len(training_features) < 2:
            raise ValueError("Need at least 2 training sessions")
        
        # Convert to numpy array
        X_train = np.array(training_features)
        self.feature_dim = X_train.shape[1]
        
        print(f"Training on {X_train.shape[0]} sessions with {self.feature_dim} features each")
        
        # Normalize features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_train)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=100,
            max_samples='auto',
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_scaled)
        self.is_trained = True
        
        # Calculate training statistics
        predictions = self.model.predict(X_scaled)
        anomaly_count = np.sum(predictions == -1)
        
        stats = {
            'n_sessions': X_train.shape[0],
            'n_features': self.feature_dim,
            'anomalies_in_training': int(anomaly_count),
            'contamination': self.contamination
        }
        
        # Save model if requested
        if save_model:
            self.save_model()
        
        print(f"Training complete: {stats}")
        return stats
    
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
        
        if self.feature_dim and len(current_features) != self.feature_dim:
            raise ValueError(f"Feature dimension mismatch: expected {self.feature_dim}, got {len(current_features)}")
        
        # Prepare features
        X = np.array([current_features])
        X_scaled = self.scaler.transform(X)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]
        anomaly_score = self.model.score_samples(X_scaled)[0]
        
        # Convert to boolean and confidence
        is_anomaly = (prediction == -1)
        
        # Convert anomaly score to confidence (0-1 scale)
        # Anomaly scores are typically negative, more negative = more anomalous
        # We normalize to 0-1 where 1 = highly confident legitimate
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
        # Isolation Forest scores are typically between -0.5 and 0.5
        # Higher (closer to 0.5) = normal, Lower (closer to -0.5) = anomalous
        # We map this to 0-1 confidence scale
        
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
            print("Warning: Model not trained, nothing to save")
            return
        
        # Save model
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save scaler
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print(f"Model saved to {self.model_path}")
    
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
            
            # Infer feature dimension from scaler
            if hasattr(self.scaler, 'n_features_in_'):
                self.feature_dim = self.scaler.n_features_in_
            
            print(f"Model loaded from {self.model_path}")
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
        if not self.is_trained:
            return {'status': 'not_trained'}
        
        info = {
            'status': 'trained',
            'contamination': self.contamination,
            'n_estimators': self.model.n_estimators if self.model else None,
            'feature_dimension': self.feature_dim,
            'model_path': self.model_path
        }
        
        return info


# Example usage
if __name__ == "__main__":
    print("Testing Behavioral Authenticator")
    
    # Simulate training data (5 sessions, 21 features each)
    np.random.seed(42)
    
    # Legitimate user sessions (similar patterns)
    legitimate_sessions = []
    for i in range(5):
        # Features centered around specific values with small variance
        features = list(np.random.normal(loc=[0.05, 0.04, 0.01,  # hold time stats
                                               0.10, 0.09, 0.02,  # DD stats
                                               0.08, 0.07, 0.015, # UD stats
                                               4.5,               # typing speed
                                               0.02] +            # error rate
                                              [0.1] * 10,         # digraph timings
                                         scale=0.01, size=21))
        legitimate_sessions.append(features)
    
    # Train model
    auth = BehavioralAuthenticator(
        model_path="test_model.pkl",
        scaler_path="test_scaler.pkl"
    )
    
    stats = auth.train(legitimate_sessions)
    print(f"\nTraining stats: {stats}")
    
    # Test on legitimate pattern
    test_legit = list(np.random.normal(loc=[0.05, 0.04, 0.01, 0.10, 0.09, 0.02, 
                                             0.08, 0.07, 0.015, 4.5, 0.02] + [0.1]*10,
                                       scale=0.01, size=21))
    is_anomaly, confidence = auth.predict_live(test_legit)
    print(f"\nLegitimate test: anomaly={is_anomaly}, confidence={confidence:.2f}")
    
    # Test on anomalous pattern (very different)
    test_anomaly = list(np.random.normal(loc=[0.15, 0.14, 0.05, 0.20, 0.19, 0.08,
                                              0.18, 0.17, 0.06, 2.0, 0.15] + [0.3]*10,
                                        scale=0.02, size=21))
    is_anomaly, confidence = auth.predict_live(test_anomaly)
    print(f"Anomalous test: anomaly={is_anomaly}, confidence={confidence:.2f}")
    
    # Test model info
    print(f"\nModel info: {auth.get_model_info()}")
