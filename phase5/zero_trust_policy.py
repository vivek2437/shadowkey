
import time

class PolicyEngine:
    """
    Evaluates risk scores against defined policies to return an action.
    """
    ACTION_ALLOW = "ALLOW"
    ACTION_STEP_UP = "STEP_UP"
    ACTION_BLOCK = "BLOCK"
    
    def __init__(self, config=None):
        self.config = config or {}
        # Thresholds
        self.trust_threshold = self.config.get("trust_threshold", 0.7)
        self.block_threshold = self.config.get("block_threshold", 0.3)
        self.max_inactivity = self.config.get("max_inactivity_seconds", 300) # 5 mins
        
    def evaluate(self, session_context, risk_score):
        """
        session_context: {
            "last_active": timestamp,
            "device_trust": float, # 1.0 = trusted
            "location_change": bool,
            "failed_attempts": int
        }
        risk_score: Float [0, 1]. 0 = Safe, 1 = Compromised.
        (Note: In fusion_dl.py I returned 'risk_score' where ~0.5 was StepUp. 
         Let's align: Risk 0.0 -> Safe, Risk 1.0 -> Bad.)
        """
        
        current_time = time.time()
        last_active = session_context.get("last_active", current_time)
        inactivity = current_time - last_active
        
        # Rule 1: Timeout (Session Drift)
        if inactivity > self.max_inactivity:
            return self.ACTION_STEP_UP, "Session timed out (Inactivity)"
            
        # Rule 2: Risk Score Limits
        if risk_score > (1.0 - self.block_threshold): # e.g. > 0.7 risk
            return self.ACTION_BLOCK, f"High Risk Score detected ({risk_score:.2f})"
            
        if risk_score > (1.0 - self.trust_threshold): # e.g. > 0.3 risk
            return self.ACTION_STEP_UP, f"Medium Risk Score ({risk_score:.2f})"
            
        # Rule 3: Context-based
        if session_context.get("location_change", False):
            return self.ACTION_STEP_UP, "Location change detected"
            
        return self.ACTION_ALLOW, "Trust verified"

