
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
import random
try:
    import onnx
    import onnxruntime as ort
except ImportError:
    onnx = None
    ort = None

class KeystrokeLSTM(nn.Module):
    """
    Bi-LSTM Autoencoder for Keystroke Dynamics.
    Encoder maps sequence -> embedding.
    Decoder reconstruction -> anomaly score.
    """
    def __init__(self, input_dim=4, hidden_dim=64, embedding_dim=32, num_layers=2):
        super(KeystrokeLSTM, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.embedding_dim = embedding_dim
        self.num_layers = num_layers
        
        # Encoder
        self.encoder_lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True
        )
        self.encoder_fc = nn.Linear(hidden_dim * 2, embedding_dim) # *2 for bidirectional
        
        # Decoder
        self.decoder_fc = nn.Linear(embedding_dim, hidden_dim * 2)
        self.decoder_lstm = nn.LSTM(
            input_size=hidden_dim * 2,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True
        )
        self.output_fc = nn.Linear(hidden_dim * 2, input_dim)

    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        
        # Encoding
        # enc_out: (batch, seq_len, hidden*2)
        # h_n: (num_layers*2, batch, hidden)
        enc_out, (h_n, c_n) = self.encoder_lstm(x)
        
        # Extract last time step from forward path and first from backward path
        # Or just pool the last layer's hidden state.
        # Simple approach: Max pool over time or take last state.
        # Let's take global max pooling over the sequence for robustness
        # enc_out dimension: (batch, seq, hidden*2)
        pooled_context = torch.max(enc_out, dim=1)[0] # (batch, hidden*2)
        
        embedding = self.encoder_fc(pooled_context) # (batch, embedding_dim)
        
        # Decoding
        # Expand embedding back to sequence length? 
        # Strategy: Repeat embedding seq_len times
        seq_len = x.size(1)
        dataset_expand = self.decoder_fc(embedding).unsqueeze(1).repeat(1, seq_len, 1) # (batch, seq, hidden*2)
        
        dec_out, _ = self.decoder_lstm(dataset_expand) # (batch, seq, hidden*2)
        reconstruction = self.output_fc(dec_out) # (batch, seq, input_dim)
        
        return reconstruction, embedding

class KeystrokeDLModel:
    def __init__(self, model_path="models/keystroke_dl.pth", config=None):
        self.model_path = model_path
        self.config = config or {}
        self.sequence_length = self.config.get("sequence_length", 50)
        self.input_dim = 4
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.model = KeystrokeLSTM(
            input_dim=self.input_dim,
            hidden_dim=self.config.get("hidden_dim", 64),
            embedding_dim=self.config.get("embedding_dim", 32),
            num_layers=self.config.get("layers", 2)
        ).to(self.device)
        
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)

    def train(self, sequences, epochs=50, batch_size=32):
        """
        Train the autoencoder on normal user data.
        sequences: List or np.array of shape (N, seq_len, 4)
        """
        self.model.train()
        dataset = torch.tensor(sequences, dtype=torch.float32).to(self.device)
        data_loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        print(f"Starting training for {epochs} epochs on {self.device}...")
        
        for epoch in range(epochs):
            total_loss = 0
            for batch in data_loader:
                self.optimizer.zero_grad()
                reconstruction, _ = self.model(batch)
                loss = self.criterion(reconstruction, batch)
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item()
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss / len(data_loader):.4f}")
                
        self.save_model()

    def predict(self, sequence):
        """
        Infer trust score from a single sequence.
        Returns: (anamoly_score, embedding)
        High anomaly score = Low Trust.
        """
        self.model.eval()
        with torch.no_grad():
            inp = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0).to(self.device) # (1, seq, 4)
            recon, embedding = self.model(inp)
            loss = self.criterion(recon, inp).item()
            
        return loss, embedding.cpu().numpy().flatten()

    def save_model(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': self.config
        }, self.model_path)
        print(f"Model saved to {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            checkpoint = torch.load(self.model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            print(f"Model loaded from {self.model_path}")
            return True
        return False

    def export_onnx(self, onnx_path):
        """Export model to ONNX format."""
        self.model.eval()
        dummy_input = torch.randn(1, self.sequence_length, self.input_dim).to(self.device)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(onnx_path), exist_ok=True)
        
        torch.onnx.export(
            self.model,
            dummy_input,
            onnx_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['reconstruction', 'embedding'],
            dynamic_axes={'input': {0: 'batch_size'}, 'reconstruction': {0: 'batch_size'}, 'embedding': {0: 'batch_size'}}
        )
        print(f"Model exported to ONNX: {onnx_path}")

if __name__ == "__main__":
    # Test stub
    print("Testing KeystrokeDLModel...")
    
    # 1. Instantiate
    ks_model = KeystrokeDLModel(model_path="test_ks_model.pth", config={"sequence_length": 10})
    
    # 2. Generate fake data: 100 sequences, length 10, 4 features
    dummy_data = np.random.rand(100, 10, 4)
    
    # 3. Train
    ks_model.train(dummy_data, epochs=5)
    
    # 4. Predict
    score, emb = ks_model.predict(dummy_data[0])
    print(f"Prediction Score (Loss): {score:.4f}")
    print(f"Embedding Shape: {emb.shape}")
    
    # 5. Export ONNX
    ks_model.export_onnx("test_ks_model.onnx")
    
    # Cleanup
    if os.path.exists("test_ks_model.pth"):
        os.remove("test_ks_model.pth")
    if os.path.exists("test_ks_model.onnx"):
        os.remove("test_ks_model.onnx")
    print("Test Complete.")
