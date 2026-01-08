
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import os
import json

class VoiceEmbeddingModel(nn.Module):
    """
    CNN-LSTM network for generating fixed-length speaker embeddings.
    Input: Mel-Spectrogram (batch, n_mels, time_steps)
    Output: Embedding vector (batch, embedding_dim)
    """
    def __init__(self, n_mels=80, embedding_dim=192, hidden_dim=128):
        super(VoiceEmbeddingModel, self).__init__()
        
        # 1D Conv blocks to extract local features from Mel-frequency
        # Treating n_mels as channels if we view it as (batch, n_mels, time)
        # But wait, typically Conv1d convolved over time. 
        # Input shape: (batch, n_mels, time)
        
        self.conv1 = nn.Conv1d(in_channels=n_mels, out_channels=128, kernel_size=5, stride=1, padding=2)
        self.bn1 = nn.BatchNorm1d(128)
        self.relu = nn.ReLU()
        
        self.conv2 = nn.Conv1d(in_channels=128, out_channels=128, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm1d(128)
        
        self.conv3 = nn.Conv1d(in_channels=128, out_channels=256, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm1d(256)
        
        self.pool = nn.MaxPool1d(kernel_size=2)
        
        # LSTM to aggregate temporal information
        self.lstm = nn.LSTM(input_size=256, hidden_size=hidden_dim, num_layers=2, batch_first=True, bidirectional=True)
        
        # Attention or Stats Pooling (Mean+Std)
        # Here we use Stats Pooling (concatenating mean and std of LSTM outputs)
        self.fc_emb = nn.Linear(hidden_dim * 2 * 2, embedding_dim) # *2 bidir, *2 mean+std
        
    def forward(self, x):
        # x: (batch, n_mels, time)
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool(x)
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.relu(self.bn3(self.conv3(x)))
        
        # Permute for LSTM: (batch, features, time) -> (batch, time, features)
        x = x.permute(0, 2, 1)
        
        self.lstm.flatten_parameters()
        lstm_out, _ = self.lstm(x) # (batch, time, hidden*2)
        
        # Statistics Pooling
        mean = torch.mean(lstm_out, dim=1)
        std = torch.std(lstm_out, dim=1)
        stats = torch.cat((mean, std), dim=1) # (batch, hidden*4)
        
        embedding = self.fc_emb(stats)
        # Normalize embedding to unit sphere
        embedding = F.normalize(embedding, p=2, dim=1)
        
        return embedding

class VoiceBiometricSystem:
    def __init__(self, model_path="models/voice_dl.pth", config=None):
        self.model_path = model_path
        self.config = config or {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.model = VoiceEmbeddingModel(
            n_mels=self.config.get("n_mels", 80),
            embedding_dim=self.config.get("embedding_dim", 192)
        ).to(self.device)
        
        self.enrolled_embeddings = {} # user_id -> np.array (centroid)
        self.threshold = self.config.get("threshold", 0.75)
        
    def extract_embedding(self, audio_features):
        """
        audio_features: (n_mels, time) numpy array or tensor
        """
        self.model.eval()
        with torch.no_grad():
             # Add batch dimension
            if isinstance(audio_features, np.ndarray):
                inp = torch.tensor(audio_features, dtype=torch.float32).unsqueeze(0).to(self.device)
            else:
                inp = audio_features.unsqueeze(0).to(self.device)
            
            emb = self.model(inp)
            return emb.cpu().numpy().flatten()
            
    def enroll_user(self, user_id, audio_samples):
        """
        Create an enrolled profile (centroid embedding) for a user.
        audio_samples: list of (n_mels, time) arrays
        """
        embeddings = []
        for sample in audio_samples:
            emb = self.extract_embedding(sample)
            embeddings.append(emb)
            
        if not embeddings:
            return False
            
        # Calculate centroid
        centroid = np.mean(embeddings, axis=0)
        centroid = centroid / np.linalg.norm(centroid) # re-normalize
        self.enrolled_embeddings[user_id] = centroid
        
        # Save enrollment database
        self.save_enrollment()
        return True
        
    def verify_user(self, user_id, audio_features):
        """
        Verify if audio belongs to user_id.
        Returns: (is_match, similarity_score)
        """
        if user_id not in self.enrolled_embeddings:
            print(f"User {user_id} not enrolled.")
            return False, 0.0
            
        target_emb = self.enrolled_embeddings[user_id]
        probe_emb = self.extract_embedding(audio_features)
        
        # Cosine similarity
        score = np.dot(target_emb, probe_emb) # vectors are unit normalized
        
        return score >= self.threshold, float(score)

    def train_step(self, anchor, positive, negative, optimizer, margin=0.2):
        """
        Single triplet loss training step.
        """
        self.model.train()
        optimizer.zero_grad()
        
        emb_a = self.model(anchor.to(self.device))
        emb_p = self.model(positive.to(self.device))
        emb_n = self.model(negative.to(self.device))
        
        # Triplet Loss: max(d(a,p) - d(a,n) + margin, 0)
        # Cosine distance = 1 - similarity
        # But F.triplet_margin_loss uses Euclidean distance by default.
        # Let's use Euclidean distance on normalized embeddings (equivalent to cosine)
        
        criterion = nn.TripletMarginLoss(margin=margin, p=2)
        loss = criterion(emb_a, emb_p, emb_n)
        
        loss.backward()
        optimizer.step()
        
        return loss.item()

    def save_model(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        torch.save(self.model.state_dict(), self.model_path)
        
    def save_enrollment(self):
        # Save enrolled embeddings to disk (simulated DB)
        path = self.model_path + ".enroll.npy"
        np.save(path, self.enrolled_embeddings)
        
    def load_model(self):
        if os.path.exists(self.model_path):
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
        
        enroll_path = self.model_path + ".enroll.npy"
        if os.path.exists(enroll_path):
            self.enrolled_embeddings = np.load(enroll_path, allow_pickle=True).item()

if __name__ == "__main__":
    # Test
    print("Testing VoiceBiometricSystem...")
    vbs = VoiceBiometricSystem(config={"n_mels": 40})
    
    # Fake audio features: (40, 100)
    fake_audio = np.random.randn(40, 100).astype(np.float32)
    
    emb = vbs.extract_embedding(fake_audio)
    print(f"Embedding shape: {emb.shape}")
    
    # Enroll
    vbs.enroll_user("user1", [fake_audio, fake_audio])
    
    # Verify
    match, score = vbs.verify_user("user1", fake_audio)
    print(f"Verification: {match}, Score: {score:.4f}")
    
    # Save
    vbs.save_model()
    print("Parameters saved.")
