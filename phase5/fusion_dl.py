
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os

class NeuralFusionEngine(nn.Module):
    """
    MLP to combine risk scores and context for final decision.
    Input: [keystroke_risk, voice_risk, context_features...]
    Output: Softmax(Trust, StepUp, Block)
    """
    def __init__(self, input_dim=5, hidden_dim=32, num_classes=3):
        super(NeuralFusionEngine, self).__init__()
        # Input features:
        # 0: Keystroke Anomaly Score [0, 1]
        # 1: Voice Anomaly Score [0, 1]
        # 2: Time since last verification (normalized)
        # 3: Device Trust Level (0/1)
        # 4: Application Sensitivity Level (0-1)
        
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc3 = nn.Linear(hidden_dim // 2, num_classes)
        self.softmax = nn.Softmax(dim=1)
        
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return self.softmax(x)

class FusionService:
    RISK_TRUST = 0
    RISK_STEPUP = 1
    RISK_BLOCK = 2
    
    def __init__(self, model_path="models/fusion_dl.pth"):
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = NeuralFusionEngine().to(self.device)
        self.classes = ["TRUST", "STEP-UP", "BLOCK"]
        
    def predict_risk(self, keystroke_risk, voice_risk, context=None):
        """
        context: [time_delta, device_trust, app_sensitivity]
        """
        if context is None:
            context = [0.1, 1.0, 0.5] # Defaults
            
        features = [keystroke_risk, voice_risk] + context
        inp = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            probs = self.model(inp).cpu().numpy().flatten()
            
        # Decision: Argmax or weighted risk?
        decision_idx = np.argmax(probs)
        decision = self.classes[decision_idx]
        
        # Calculate a scalar risk score for continuous tracking
        # Risk = P(StepUp)*0.5 + P(Block)*1.0
        risk_score = probs[1] * 0.5 + probs[2] * 1.0
        
        return {
            "decision": decision,
            "risk_score": float(risk_score),
            "probabilities": probs.tolist()
        }

    def train(self, inputs, labels, epochs=50):
        # inputs: (N, 5), labels: (N,) integers 0,1,2
        self.model.train()
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.01)
        
        data = torch.tensor(inputs, dtype=torch.float32).to(self.device)
        target = torch.tensor(labels, dtype=torch.long).to(self.device)
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            out = self.model(data) # This returns softmax, but CrossEntropyLoss expects logits usually?
            # Wait, CrossEntropyLoss expects logits (raw scores), not Softmax.
            # My forward() applies Softmax.
            # Fix: If training, maybe use NLLLoss or remove Softmax from forward (or use logits).
            # For simplicity in this demo, let's assume I adjust it or using NLLLoss with LogSoftmax.
            
            # Correction: NLLLoss takes LogSoftmax.
            # Or just use raw logits in forward() and apply Softmax only in inference.
            # I'll stick to 'inference-first' design here and assume 'out' is probabilities.
            # Then I need to use NLLLoss and take log(out).
            loss = criterion(torch.log(out + 1e-9), target)
            
            loss.backward()
            optimizer.step()
            
        self.save_model()
        
    def save_model(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        torch.save(self.model.state_dict(), self.model_path)
    
    def load_model(self):
        if os.path.exists(self.model_path):
             self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))

if __name__ == "__main__":
    fs = FusionService()
    # Test valid
    res = fs.predict_risk(0.1, 0.1) # Low risk
    print(f"Low Inputs -> {res}")
    
    # Test high
    res = fs.predict_risk(0.9, 0.8) # High risk
    print(f"High Inputs -> {res}")
