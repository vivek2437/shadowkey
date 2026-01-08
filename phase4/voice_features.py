"""
ShadowKey Phase 4 - Voice Feature Extraction
Extracts biometric features from raw audio data using librosa.
"""

import numpy as np
import logging
import warnings
from typing import List, Optional, Dict, Union

try:
    import librosa
except Exception as e:
    librosa = None
    print(f"Warning: 'librosa' library issue ({e}). using fallback feature extraction.")

# Suppress librosa warnings
warnings.filterwarnings('ignore')

class VoiceFeatureExtractor:
    """
    Extracts behavioral/biometric features from voice samples.
    """
    
    def __init__(self, sample_rate: int = 22050, n_mfcc: int = 13):
        """
        Initialize feature extractor.
        
        Args:
            sample_rate: Audio sample rate (must match capture)
            n_mfcc: Number of MFCC coefficients to extract
        """
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc
        self.logger = logging.getLogger(__name__)

    def _compute_fallback_features(self, audio_data: np.ndarray) -> Optional[np.ndarray]:
        """Compute basic features using only NumPy (Fallback)."""
        try:
            # 1. RMS Energy
            rms = np.sqrt(np.mean(audio_data**2))
            
            # 2. Zero Crossing Rate
            zcr = ((audio_data[:-1] * audio_data[1:]) < 0).sum() / len(audio_data)
            
            # 3. FFT (Spectral features approximation)
            fft_vals = np.fft.rfft(audio_data)
            fft_mag = np.abs(fft_vals)
            freqs = np.fft.rfftfreq(len(audio_data), 1/self.sample_rate)
            
            # Spectral Centroid approx
            spec_cent = np.sum(freqs * fft_mag) / (np.sum(fft_mag) + 1e-6)
            
            # Spectral Bandwidth approx
            spec_bw = np.sqrt(np.sum(((freqs - spec_cent)**2) * fft_mag) / (np.sum(fft_mag) + 1e-6))
            
            # Create a vector of similar size to librosa version (approx 33-35 dims)
            # We'll just pad with FFT energy in buckets
            features_list = [spec_cent, spec_bw, zcr, rms]
            
            # Add some FFT bins as "MFCC-like" features
            # Take log magnitude of first 13 bins (averaged) to mimic MFCCs
            n_bins = self.n_mfcc
            chunk_size = max(1, len(fft_mag) // n_bins)
            for i in range(n_bins):
                start = i * chunk_size
                end = (i+1) * chunk_size
                if start >= len(fft_mag):
                    val = 0
                else:
                    val = np.mean(fft_mag[start:end]) if end > start else fft_mag[start]
                features_list.append(np.log(val + 1e-6))
                features_list.append(0.0) # Std dev placeholder
            
            # Pad to ensure length matches expectation if needed, or just return what we have
            # Pitch placeholders (mean, std) + Spectral Rolloff placeholder
            features_list.append(0.0) # Rolloff
            features_list.append(0.0) # Pitch Mean
            features_list.append(0.0) # Pitch Std
            
            return np.array(features_list)
        except Exception as e:
            self.logger.error(f"Fallback extraction error: {e}")
            return None

    def extract_features(self, audio_data: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract fixed-length feature vector from audio sample.
        """
        if len(audio_data) == 0:
            self.logger.warning("Empty audio data provided")
            return None
            
        # Try Librosa if available
        if librosa is not None:
            try:
                # Ensure audio is properly trimmed (remove silence)
                y, _ = librosa.effects.trim(audio_data, top_db=20)
                
                if len(y) < self.sample_rate * 0.1: # Relaxed length check
                    # Too short for full processing? fall back or return early
                    if len(y) == 0: return None
                
                features_list = []
                
                # 1. MFCCs
                mfcc = librosa.feature.mfcc(y=y, sr=self.sample_rate, n_mfcc=self.n_mfcc)
                features_list.extend(np.mean(mfcc, axis=1)) 
                features_list.extend(np.std(mfcc, axis=1)) 
                
                # 2. Spectral Centroid
                spec_cent = librosa.feature.spectral_centroid(y=y, sr=self.sample_rate)
                features_list.append(np.mean(spec_cent))
                
                # 3. Spectral Bandwidth
                spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=self.sample_rate)
                features_list.append(np.mean(spec_bw))
                
                # 4. Spectral Rolloff
                spec_roll = librosa.feature.spectral_rolloff(y=y, sr=self.sample_rate)
                features_list.append(np.mean(spec_roll))
                
                # 5. Zero Crossing Rate
                zcr = librosa.feature.zero_crossing_rate(y)
                features_list.append(np.mean(zcr))
                
                # 6. RMS Energy
                rms = librosa.feature.rms(y=y)
                features_list.append(np.mean(rms))
                
                # 7. Pitch (F0)
                try:
                    f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
                    f0 = f0[~np.isnan(f0)]
                    if len(f0) > 0:
                        features_list.append(np.mean(f0))
                        features_list.append(np.std(f0))
                    else:
                        features_list.append(0.0)
                        features_list.append(0.0)
                except:
                    features_list.append(0.0)
                    features_list.append(0.0)
                    
                return np.array(features_list)
                
            except Exception as e:
                self.logger.warning(f"Librosa failed at runtime ({e}), using fallback.")
                # Fall through to fallback
        
        # Fallback
        return self._compute_fallback_features(audio_data)

    def get_feature_names(self) -> List[str]:
        names = []
        for i in range(self.n_mfcc): names.append(f"mfcc_mean_{i}")
        for i in range(self.n_mfcc): names.append(f"mfcc_std_{i}")
        names.extend(["spectral_centroid", "spectral_bandwidth", "spectral_rolloff", "zcr", "rms", "pitch_mean", "pitch_std"])
        return names
