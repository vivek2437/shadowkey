"""
ShadowKey Phase 3 - Feature Extraction Module
Enhanced feature extraction with hold time, flight time, digraphs, trigraphs, speed, errors,
Shannon entropy, rhythm stability, and rolling statistics.
"""

import statistics
import math
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import time


@dataclass
class KeyEvent:
    """Simple representation of a key event."""
    key: str
    event_type: str  # 'down' or 'up'
    timestamp: float


class FeatureExtractor:
    """
    Comprehensive feature extraction for keystroke dynamics.
    Calculates hold time, flight time, digraphs, trigraphs, speed, and error metrics.
    """
    
    def __init__(self):
        """Initialize feature extractor with empty state."""
        # State tracking
        self.key_down_times: Dict[str, float] = {}  # key -> timestamp when pressed
        self.last_key_up_time: Optional[float] = None
        self.session_start_time: Optional[float] = None
        
        # Feature storage
        self.hold_times: List[float] = []  # Time key was held down
        self.flight_times_dd: List[float] = []  # Down-down intervals
        self.flight_times_ud: List[float] = []  # Up-down intervals
        self.digraph_timings: Dict[str, List[float]] = defaultdict(list)
        self.trigraph_timings: Dict[str, List[float]] = defaultdict(list)
        self.key_sequence: List[str] = []  # Track key sequence for entropy
        self.error_keys = {'[backspace]', '[delete]', '[BackSpace]', '[Delete]'}
        self.error_count = 0
        self.total_keystrokes = 0
        
        # Last key tracking for n-grams
        self.last_key: Optional[str] = None
        self.second_last_key: Optional[str] = None
        self.last_key_down_time: Optional[float] = None
    
    def process_events(self, events: List[KeyEvent]) -> None:
        """
        Process a batch of keystroke events and extract features.
        
        Args:
            events: List of KeyEvent objects to process
        """
        for event in events:
            self._process_single_event(event)
    
    def _process_single_event(self, event: KeyEvent) -> None:
        """
        Process a single keystroke event.
        
        Args:
            event: KeyEvent to process
        """
        # Track session timing
        if self.session_start_time is None:
            self.session_start_time = event.timestamp
        
        key = event.key.lower() # Normalize key for consistency
        
        # Handle key down events
        if event.event_type == 'down':
            # Track error keys
            if key in self.error_keys:
                self.error_count += 1
            
            # Calculate DD interval (down-to-down)
            if self.last_key_down_time is not None:
                dd_interval = event.timestamp - self.last_key_down_time
                if dd_interval > 0:  # Sanity check
                    self.flight_times_dd.append(dd_interval)
            
            # Calculate UD interval (up-to-down) - Flight time
            if self.last_key_up_time is not None:
                ud_interval = event.timestamp - self.last_key_up_time
                if ud_interval > 0:
                    self.flight_times_ud.append(ud_interval)
            
            # Track key down
            self.key_down_times[key] = event.timestamp
            self.key_sequence.append(key)  # Add to sequence for entropy
            self.last_key_down_time = event.timestamp
            
            # Build key sequence for digraphs/trigraphs
            if key not in self.error_keys and key not in ['[shift]', '[ctrl]', '[alt]']:
                self.total_keystrokes += 1
                
                # Extract digraph timing
                if self.last_key is not None:
                    digraph = self.last_key + key
                    if self.last_key_down_time and len(self.flight_times_dd) > 0:
                        self.digraph_timings[digraph].append(self.flight_times_dd[-1])
                
                # Extract trigraph timing
                if self.second_last_key is not None and self.last_key is not None:
                    trigraph = self.second_last_key + self.last_key + key
                    if len(self.flight_times_dd) >= 2:
                        # Average timing for the trigraph
                        avg_timing = statistics.mean(self.flight_times_dd[-2:])
                        self.trigraph_timings[trigraph].append(avg_timing)
                
                self.second_last_key = self.last_key
                self.last_key = key
        
        # Handle key up events
        elif event.event_type == 'up':
            # Calculate hold time
            if key in self.key_down_times:
                hold_time = event.timestamp - self.key_down_times[key]
                if hold_time > 0:  # Sanity check
                    self.hold_times.append(hold_time)
                del self.key_down_times[key]
            
            self.last_key_up_time = event.timestamp
    
    def get_typing_speed(self) -> Tuple[float, float]:
        """
        Calculate typing speed metrics.
        
        Returns:
            Tuple of (characters_per_second, words_per_minute)
        """
        if not self.session_start_time or self.total_keystrokes == 0:
            return 0.0, 0.0
        
        elapsed_time = time.time() - self.session_start_time
        if elapsed_time == 0:
            return 0.0, 0.0
        
        cps = self.total_keystrokes / elapsed_time
        wpm = (self.total_keystrokes / 5) / (elapsed_time / 60)  # Assume 5 chars per word
        
        return round(cps, 2), round(wpm, 2)
    
    def get_sequence_entropy(self) -> float:
        """
        Calculate Shannon entropy of key sequence.
        Measures randomness/unpredictability of typing patterns.
        
        Returns:
            Entropy value (higher = more varied/random)
        """
        if not self.key_sequence:
            return 0.0
        
        # Count frequency of each key
        key_counts = Counter(self.key_sequence)
        total_keys = len(self.key_sequence)
        
        # Calculate Shannon entropy
        entropy = 0.0
        for count in key_counts.values():
            probability = count / total_keys
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return round(entropy, 4)
    
    def get_rhythm_stability(self, window_size: int = 10) -> float:
        """
        Calculate rhythm stability based on variance of flight times.
        Lower values indicate more consistent typing rhythm.
        
        Args:
            window_size: Size of rolling window for calculation
            
        Returns:
            Variance of flight times (lower = more stable)
        """
        if len(self.flight_times_ud) < window_size:
            # Not enough data, return variance of all available data
            if len(self.flight_times_ud) < 2:
                return 0.0
            return round(statistics.variance(self.flight_times_ud), 4)
        
        # Use last N flight times for rolling window
        recent_flights = self.flight_times_ud[-window_size:]
        return round(statistics.variance(recent_flights), 4)
    
    def get_rolling_speed_stats(self, window_size: int = 30) -> Dict[str, float]:
        """
        Calculate rolling statistics for typing speed.
        
        Args:
            window_size: Size of rolling window
            
        Returns:
            Dictionary with rolling mean and standard deviation
        """
        if len(self.flight_times_dd) < 2:
            return {'rolling_mean': 0.0, 'rolling_std': 0.0}
        
        # Use recent flight times to estimate speed
        recent_flights = self.flight_times_dd[-window_size:] if len(self.flight_times_dd) >= window_size else self.flight_times_dd
        
        # Convert to speed (keys per second)
        speeds = [1.0 / ft if ft > 0 else 0 for ft in recent_flights]
        
        rolling_mean = statistics.mean(speeds) if speeds else 0.0
        rolling_std = statistics.stdev(speeds) if len(speeds) > 1 else 0.0
        
        return {
            'rolling_mean': round(rolling_mean, 4),
            'rolling_std': round(rolling_std, 4)
        }
    
    def get_feature_summary(self) -> Dict[str, any]:
        """
        Get human-readable feature summary with Phase 3 enhancements.
        
        Returns:
            Dictionary of feature statistics
        """
        cps, wpm = self.get_typing_speed()
        entropy = self.get_sequence_entropy()
        rhythm_stability = self.get_rhythm_stability()
        rolling_stats = self.get_rolling_speed_stats()
        
        summary = {
            'total_keystrokes': self.total_keystrokes,
            'error_count': self.error_count,
            'typing_speed_cps': cps,
            'typing_speed_wpm': wpm,
            'avg_hold_time': statistics.mean(self.hold_times) if self.hold_times else 0,
            'avg_flight_time_dd': statistics.mean(self.flight_times_dd) if self.flight_times_dd else 0,
            'avg_flight_time_ud': statistics.mean(self.flight_times_ud) if self.flight_times_ud else 0,
            'unique_digraphs': len(self.digraph_timings),
            'unique_trigraphs': len(self.trigraph_timings),
            'sequence_entropy': entropy,
            'rhythm_stability': rhythm_stability,
            'rolling_speed_mean': rolling_stats['rolling_mean'],
            'rolling_speed_std': rolling_stats['rolling_std']
        }
        
        # Round floats for readability
        for key, value in summary.items():
            if isinstance(value, float):
                summary[key] = round(value, 4)
        
        return summary
    
    def get_feature_vector(self, top_n_digraphs: int = 10) -> List[float]:
        """
        Get numerical feature vector for ML training/prediction.
        Includes Phase 3 enhanced features.
        
        Args:
            top_n_digraphs: Number of top digraphs to include
            
        Returns:
            List of numerical features
        """
        vector = []
        
        # Basic statistics
        vector.append(self.total_keystrokes)
        vector.append(self.error_count)
        
        # Typing speed
        cps, wpm = self.get_typing_speed()
        vector.append(cps)
        vector.append(wpm)
        
        # Hold time stats
        if self.hold_times:
            vector.append(statistics.mean(self.hold_times))
            vector.append(statistics.stdev(self.hold_times) if len(self.hold_times) > 1 else 0)
            vector.append(min(self.hold_times))
            vector.append(max(self.hold_times))
        else:
            vector.extend([0, 0, 0, 0])
        
        # Flight time stats (down-down)
        if self.flight_times_dd:
            vector.append(statistics.mean(self.flight_times_dd))
            vector.append(statistics.stdev(self.flight_times_dd) if len(self.flight_times_dd) > 1 else 0)
        else:
            vector.extend([0, 0])
        
        # Flight time stats (up-down)
        if self.flight_times_ud:
            vector.append(statistics.mean(self.flight_times_ud))
            vector.append(statistics.stdev(self.flight_times_ud) if len(self.flight_times_ud) > 1 else 0)
        else:
            vector.extend([0, 0])
        
        # Top digraph timings
        top_digraphs = self._get_top_digraphs(top_n_digraphs)
        for i in range(top_n_digraphs):
            if i < len(top_digraphs):
                vector.append(top_digraphs[i][1])  # Average timing
            else:
                vector.append(0)  # Pad with zeros
        
        # Phase 3 enhanced features
        vector.append(self.get_sequence_entropy())
        vector.append(self.get_rhythm_stability())
        
        rolling_stats = self.get_rolling_speed_stats()
        vector.append(rolling_stats['rolling_mean'])
        vector.append(rolling_stats['rolling_std'])
        
        return vector
    
    def _get_top_digraphs(self, n: int) -> List[Tuple[str, float]]:
        """
        Get top N most frequent digraphs with average timing.
        
        Args:
            n: Number of top digraphs to return
            
        Returns:
            List of (digraph, avg_timing) tuples
        """
        digraph_avgs = []
        for digraph, timings in self.digraph_timings.items():
            if timings: # Ensure there are timings to average
                avg_timing = statistics.mean(timings)
                digraph_avgs.append((digraph, avg_timing))
        
        # Sort by frequency (number of occurrences)
        # Need to ensure digraph exists in self.digraph_timings for len()
        digraph_avgs.sort(key=lambda x: len(self.digraph_timings.get(x[0], [])), reverse=True)
        return digraph_avgs[:n]
    
    def _get_top_trigraphs(self, n: int) -> List[Tuple[str, float]]:
        """
        Get top N most frequent trigraphs with average timing.
        
        Args:
            n: Number of top trigraphs to return
            
        Returns:
            List of (trigraph, avg_timing) tuples
        """
        trigraph_avgs = []
        for trigraph, timings in self.trigraph_timings.items():
            if timings: # Ensure there are timings to average
                avg_timing = statistics.mean(timings)
                trigraph_avgs.append((trigraph, avg_timing))
        
        # Sort by frequency
        # Need to ensure trigraph exists in self.trigraph_timings for len()
        trigraph_avgs.sort(key=lambda x: len(self.trigraph_timings.get(x[0], [])), reverse=True)
        return trigraph_avgs[:n]
    
    def reset(self) -> None:
        """Reset all feature data for new session."""
        self.key_down_times.clear()
        self.last_key_up_time = None
        self.session_start_time = None
        self.hold_times.clear()
        self.flight_times_dd.clear()
        self.flight_times_ud.clear()
        self.digraph_timings.clear()
        self.trigraph_timings.clear()
        self.key_sequence.clear()
        self.error_count = 0
        self.total_keystrokes = 0
        self.last_key = None
        self.second_last_key = None
        self.last_key_down_time = None


# Example usage
if __name__ == "__main__":
    print("Testing Feature Extractor")
    
    # Simulate some keystrokes
    extractor = FeatureExtractor()
    
    events = [
        KeyEvent('h', 'down', 0.0),
        KeyEvent('h', 'up', 0.05),
        KeyEvent('e', 'down', 0.1),
        KeyEvent('e', 'up', 0.15),
        KeyEvent('l', 'down', 0.2),
        KeyEvent('l', 'up', 0.25),
        KeyEvent('l', 'down', 0.3),
        KeyEvent('l', 'up', 0.35),
        KeyEvent('o', 'down', 0.4),
        KeyEvent('o', 'up', 0.45),
    ]
    
    extractor.process_events(events)
    
    print("\nFeature Summary:")
    summary = extractor.get_feature_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    print("\nFeature Vector:")
    vector = extractor.get_feature_vector()
    print(vector)
