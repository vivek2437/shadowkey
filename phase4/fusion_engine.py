"""
ShadowKey Phase 4 - Multi-Modal Fusion Engine
Combines risk scores from Keystroke Dynamics and Voice Biometrics.
"""

from typing import Dict, Tuple, Optional
import json

class FusionEngine:
    """
    Decides authentication risk level based on multiple factors.
    """
    
    # Risk Levels
    RISK_LOW = 0      # Trusted
    RISK_MEDIUM = 1   # Verify (Voice/Password)
    RISK_HIGH = 2     # Deny/Lock
    
    def __init__(self, config_file: str = "config_phase4.json"):
        """
        Initialize fusion engine with configuration.
        """
        self.config_file = config_file
        self.weights = {'keystroke': 0.7, 'voice': 0.3}
        self.thresholds = {'low': 0.3, 'high': 0.7}
        
        self.load_config()
        
    def load_config(self):
        """Load fusion weights and thresholds from config."""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                config = data.get('fusion', {})
                self.weights = config.get('weights', self.weights)
                self.thresholds = config.get('thresholds', self.thresholds)
        except FileNotFoundError:
            pass # Use defaults
            
    def calculate_risk(self, keystroke_confidence: float, voice_confidence: Optional[float] = None) -> float:
        """
        Calculate combined risk score (0.0 to 1.0).
        0.0 = Safe (High Confidence), 1.0 = Risk (Low Confidence)
        
        Args:
            keystroke_confidence: 0.0-1.0 confidence from keystroke model
            voice_confidence: 0.0-1.0 confidence from voice model (Optional)
            
        Returns:
            Weighted risk score
        """
        # Convert confidence to risk (Risk = 1 - Confidence)
        k_risk = 1.0 - max(0.0, min(1.0, keystroke_confidence))
        
        if voice_confidence is not None:
            v_risk = 1.0 - max(0.0, min(1.0, voice_confidence))
            
            # Weighted sum
            w_k = self.weights.get('keystroke', 0.7)
            w_v = self.weights.get('voice', 0.3)
            
            # Normalize weights
            total_w = w_k + w_v
            w_k /= total_w
            w_v /= total_w
            
            final_risk = (k_risk * w_k) + (v_risk * w_v)
        else:
            # Fallback to just keystroke risk if no voice data
            final_risk = k_risk
            
        return final_risk
        
    def decide_auth_level(self, risk_score: float) -> int:
        """
        Determine action based on risk score.
        
        Returns:
            RISK_LOW, RISK_MEDIUM, or RISK_HIGH
        """
        if risk_score > self.thresholds['high']:
            return self.RISK_HIGH
        elif risk_score > self.thresholds['low']:
            return self.RISK_MEDIUM
        else:
            return self.RISK_LOW

if __name__ == "__main__":
    # Test
    fusion = FusionEngine()
    
    # Scene 1: Good Keystroke, Good Voice
    risk = fusion.calculate_risk(0.9, 0.9)
    print(f"Good/Good Risk: {risk:.2f} -> Level {fusion.decide_auth_level(risk)}")
    
    # Scene 2: Bad Keystroke, Good Voice (Should be Med/High depending on weights)
    risk = fusion.calculate_risk(0.2, 0.9)
    print(f"Bad/Good Risk:  {risk:.2f} -> Level {fusion.decide_auth_level(risk)}")
    
    # Scene 3: Bad Keystroke, Bad Voice
    risk = fusion.calculate_risk(0.2, 0.2)
    print(f"Bad/Bad Risk:   {risk:.2f} -> Level {fusion.decide_auth_level(risk)}")
