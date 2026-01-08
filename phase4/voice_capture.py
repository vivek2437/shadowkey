"""
ShadowKey Phase 4 - Voice Capture Module
Handles microphone recording and audio data acquisition.
"""

import time
import numpy as np
import threading
from typing import Optional, Tuple, List, Dict
import logging

try:
    import sounddevice as sd
except ImportError:
    sd = None
    print("Warning: 'sounddevice' library not found. Voice capture will not work.")

class VoiceCaptureManager:
    """
    Manages audio recording from microphone.
    """
    
    def __init__(self, sample_rate: int = 22050, channels: int = 1):
        """
        Initialize voice capture manager.
        
        Args:
            sample_rate: Sampling rate in Hz (default 22050 for librosa compatibility)
            channels: Number of audio channels (1 for mono)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.logger = logging.getLogger(__name__)
        
        if sd is None:
            self.logger.error("sounddevice not installed")
            
    def get_devices(self) -> List[Dict]:
        """
        List available audio input devices.
        
        Returns:
            List of device dictionaries
        """
        if sd is None:
            return []
            
        try:
            devices = sd.query_devices()
            input_devices = []
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    input_devices.append({
                        'id': i,
                        'name': dev['name'],
                        'channels': dev['max_input_channels'],
                        'sample_rate': dev['default_samplerate']
                    })
            return input_devices
        except Exception as e:
            self.logger.error(f"Error listing devices: {e}")
            return []

    def record_sample(self, duration: float = 3.0, device_id: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Record a fixed-duration audio sample.
        Blocking call.
        
        Args:
            duration: Duration in seconds
            device_id: Specific device ID to use (None for system default)
            
        Returns:
            Numpy array of audio data (float32) or None if failed
        """
        if sd is None:
            return None
            
        try:
            self.logger.info(f"Starting recording for {duration}s...")
            self.is_recording = True
            
            # Record audio
            # sd.rec creates a numpy array
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_id,
                dtype='float32',
                blocking=True
            )
            
            self.is_recording = False
            self.logger.info("Recording complete.")
            
            # Flatten to 1D array if mono
            if self.channels == 1:
                return recording.flatten()
            return recording
            
        except Exception as e:
            self.logger.error(f"Recording error: {e}")
            self.is_recording = False
            return None

    def check_microphone_access(self) -> bool:
        """
        Quick check if microphone is accessible.
        """
        if sd is None:
            return False
        try:
            # Try to query default input device
            sd.query_devices(kind='input')
            return True
        except Exception:
            return False

if __name__ == "__main__":
    # Test recording
    logging.basicConfig(level=logging.INFO)
    capture = VoiceCaptureManager()
    
    print("Available Devices:")
    for dev in capture.get_devices():
        print(f"  {dev['id']}: {dev['name']}")
    
    if capture.check_microphone_access():
        print("\nRecording 2 second test sample...")
        audio = capture.record_sample(duration=2.0)
        if audio is not None:
            print(f"Success! Audio shape: {audio.shape}, Max amplitude: {np.max(np.abs(audio)):.4f}")
        else:
            print("Recording failed.")
    else:
        print("Microphone not accessible.")
