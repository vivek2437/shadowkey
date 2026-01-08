
import time
import numpy as np
from .dl_keystroke_model import KeystrokeDLModel
from .dl_voice_model import VoiceBiometricSystem
from .fusion_dl import FusionService
from .zero_trust_policy import PolicyEngine

class ContinuousAuthEngine:
    def __init__(self, config=None):
        self.config = config or {}
        
        # Load Sub-Systems
        self.keystroke_model = KeystrokeDLModel()
        self.voice_model = VoiceBiometricSystem()
        self.fusion_service = FusionService()
        self.policy_engine = PolicyEngine()
        
        
        # Redis Connection
        self.redis_url = self.config.get("redis_url", "redis://localhost:6379/0")
        try:
            import redis
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            self.redis.ping() # Check connection
            self.use_redis = True
            print("Connected to Redis.")
        except (ImportError, Exception) as e:
            print(f"Redis connection failed, falling back to in-memory: {e}")
            self.use_redis = False
            self.local_sessions = {}
        
        # Try loading models (silently fail if not trained, handled at runtime)
        try:
            self.keystroke_model.load_model()
            self.voice_model.load_model()
            self.fusion_service.load_model()
        except Exception as e:
            print(f"Warning: Models not loaded fully: {e}")

    def _get_session(self, user_id):
        import json
        if self.use_redis:
            data = self.redis.get(f"session:{user_id}")
            return json.loads(data) if data else None
        else:
            return self.local_sessions.get(user_id)

    def _save_session(self, user_id, data):
        import json
        if self.use_redis:
            self.redis.set(f"session:{user_id}", json.dumps(data), ex=3600) # 1 hour TTL
        else:
            self.local_sessions[user_id] = data

    def create_session(self, user_id):
        session_data = {
            "start_time": time.time(),
            "last_active": time.time(),
            "keystroke_risk": 0.0,
            "voice_risk": 0.0,
            "current_risk": 0.0,
            "status": "ACTIVE",
            "history": []
        }
        self._save_session(user_id, session_data)
        return session_data

    def process_keystroke(self, user_id, sequence):
        """
        sequence: (seq_len, 4) array
        """
        session = self._get_session(user_id)
        if not session:
            return {"status": "INVALID_SESSION"}
            
        session["last_active"] = time.time()
        
        # DL Inference
        try:
            anomaly_score, _ = self.keystroke_model.predict(sequence)
            
            # Normalize score (assuming MSE gives ~0-1 range roughly, 
            # usually requires calibration. For now clip/sigmoid)
            # Simple heuristic:
            risk = 1.0 - (1.0 / (1.0 + anomaly_score)) # sigmoid-ish
        except Exception as e:
            print(f"Keystroke inference error: {e}")
            risk = 0.5 # Default medium risk on error
        
        session["keystroke_risk"] = risk
        self._save_session(user_id, session)
        return self._evaluate_fusion(user_id)

    def process_voice(self, user_id, audio_features):
        session = self._get_session(user_id)
        if not session:
            return {"status": "INVALID_SESSION"}
            
        session["last_active"] = time.time()
        
        # Voice Verification
        try:
            match, score_sim = self.voice_model.verify_user(user_id, audio_features)
            
            # Risk = 1 - similarity (if match)
            # If no match? Risk = 1.0
            if match:
                 # score_sim is Cosine (-1 to 1). If 1 -> risk 0.
                risk = 1.0 - max(0, score_sim)
            else:
                risk = 0.95 # High risk
        except Exception as e:
            print(f"Voice inference error: {e}")
            risk = 0.5
            
        session["voice_risk"] = risk
        self._save_session(user_id, session)
        return self._evaluate_fusion(user_id)

    def _evaluate_fusion(self, user_id):
        session = self._get_session(user_id)
        if not session: return {"status": "ERR"}
        
        # Context
        context = [
            time.time() - session["last_active"], # Time delta within session?
            1.0, # Device trust (mock)
            0.5  # App sensitivity (mock)
        ]
        
        fusion_res = self.fusion_service.predict_risk(
            session["keystroke_risk"],
            session["voice_risk"],
            context
        )
        
        session["current_risk"] = fusion_res["risk_score"]
        
        # Policy Check
        action, reason = self.policy_engine.evaluate(session, session["current_risk"])
        
        result = {
            "user_id": user_id,
            "risk_score": session["current_risk"],
            "action": action,
            "reason": reason,
            "details": fusion_res
        }
        
        session["history"].append(result)
        
        if action == "BLOCK":
            session["status"] = "BLOCKED"
        elif action == "STEP_UP":
            session["status"] = "STEP_UP_REQUIRED"
        
        self._save_session(user_id, session)
        return result

    def get_session_status(self, user_id):
        return self._get_session(user_id)
