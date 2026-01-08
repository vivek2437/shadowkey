"""
ShadowKey Phase 2 - Feature Extraction Module
Enhanced feature extraction with hold time, flight time, digraphs, trigraphs, speed, and errors.
"""

import statistics
from collections import defaultdict
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
        self.hold_times: List[float] = []
        self.dd_intervals: List[float] = []  # Down-Down
        self.ud_intervals: List[float] = []  # Up-Down
        self.digraph_timings: Dict[str, List[float]] = defaultdict(list)
        self.trigraph_timings: Dict[str, List[float]] = defaultdict(list)
        self.error_count: int = 0
        self.total_keys: int = 0
        self.session_start: Optional[float] = None
        self.session_end: Optional[float] = None
        
        # Track key states for hold time calculation
        self._key_down_times: Dict[str, float] = {}
        self._last_down_time: Optional[float] = None
        self._last_up_time: Optional[float] = None
        self._key_sequence: List[str] = []
    
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
        if self.session_start is None:
            self.session_start = event.timestamp
        self.session_end = event.timestamp
        
        # Handle key down events
        if event.event_type == 'down':
            # Track error keys
            if event.key in ['[backspace]', '[delete]', '[BackSpace]', '[Delete]']:
                self.error_count += 1
            
            # Calculate DD interval (down-to-down)
            if self._last_down_time is not None:
                dd_interval = event.timestamp - self._last_down_time
                if dd_interval > 0:  # Sanity check
                    self.dd_intervals.append(dd_interval)
            
            # Calculate UD interval (up-to-down) - Flight time
            if self._last_up_time is not None:
                ud_interval = event.timestamp - self._last_up_time
                if ud_interval > 0:
                    self.ud_intervals.append(ud_interval)
            
            # Store down time for this key
            self._key_down_times[event.key] = event.timestamp
            self._last_down_time = event.timestamp
            
            # Build key sequence for digraphs/trigraphs
            if event.key not in ['[backspace]', '[delete]', '[BackSpace]', '[Delete]', '[shift]', '[ctrl]', '[alt]']:
                self._key_sequence.append(event.key)
                self.total_keys += 1
                
                # Extract digraph timing
                if len(self._key_sequence) >= 2:
                    digraph = ''.join(self._key_sequence[-2:])
                    if self._last_down_time and len(self.dd_intervals) > 0:
                        self.digraph_timings[digraph].append(self.dd_intervals[-1])
                
                # Extract trigraph timing
                if len(self._key_sequence) >= 3:
                    trigraph = ''.join(self._key_sequence[-3:])
                    if len(self.dd_intervals) >= 2:
                        # Average timing for the trigraph
                        avg_timing = statistics.mean(self.dd_intervals[-2:])
                        self.trigraph_timings[trigraph].append(avg_timing)
        
        # Handle key up events
        elif event.event_type == 'up':
            # Calculate hold time
            if event.key in self._key_down_times:
                hold_time = event.timestamp - self._key_down_times[event.key]
                if hold_time > 0:  # Sanity check
                    self.hold_times.append(hold_time)
                del self._key_down_times[event.key]
            
            self._last_up_time = event.timestamp
    
    def get_typing_speed(self) -> Tuple[float, float]:
        """
        Calculate typing speed metrics.
        
        Returns:
            Tuple of (characters_per_second, words_per_minute)
        """
        if self.session_start is None or self.session_end is None:
            return 0.0, 0.0
        
        duration = self.session_end - self.session_start
        if duration <= 0:
            return 0.0, 0.0
        
        cps = self.total_keys / duration
        wpm = (self.total_keys / 5) / (duration / 60)  # Average word = 5 characters
        
        return cps, wpm
    
    def get_feature_summary(self) -> Dict[str, any]:
        """
        Get human-readable feature summary.
        
        Returns:
            Dictionary of feature statistics
        """
        cps, wpm = self.get_typing_speed()
        
        summary = {
            'total_keys': self.total_keys,
            'error_count': self.error_count,
            'typing_speed_cps': round(cps, 2),
            'typing_speed_wpm': round(wpm, 2),
            'hold_times': {
                'mean': round(statistics.mean(self.hold_times), 4) if self.hold_times else 0,
                'median': round(statistics.median(self.hold_times), 4) if self.hold_times else 0,
                'stdev': round(statistics.stdev(self.hold_times), 4) if len(self.hold_times) > 1 else 0,
                'count': len(self.hold_times)
            },
            'dd_intervals': {
                'mean': round(statistics.mean(self.dd_intervals), 4) if self.dd_intervals else 0,
                'median': round(statistics.median(self.dd_intervals), 4) if self.dd_intervals else 0,
                'stdev': round(statistics.stdev(self.dd_intervals), 4) if len(self.dd_intervals) > 1 else 0,
                'count': len(self.dd_intervals)
            },
            'ud_intervals': {
                'mean': round(statistics.mean(self.ud_intervals), 4) if self.ud_intervals else 0,
                'median': round(statistics.median(self.ud_intervals), 4) if self.ud_intervals else 0,
                'stdev': round(statistics.stdev(self.ud_intervals), 4) if len(self.ud_intervals) > 1 else 0,
                'count': len(self.ud_intervals)
            },
            'top_digraphs': self._get_top_digraphs(5),
            'top_trigraphs': self._get_top_trigraphs(5)
        }
        
        return summary
    
    def get_feature_vector(self, top_n_digraphs: int = 10) -> List[float]:
        """
        Get numerical feature vector for ML training/prediction.
        
        Args:
            top_n_digraphs: Number of top digraphs to include
            
        Returns:
            List of numerical features
        """
        cps, _ = self.get_typing_speed()
        
        vector = []
        
        # Hold time features
        if self.hold_times:
            vector.extend([
                statistics.mean(self.hold_times),
                statistics.median(self.hold_times),
                statistics.stdev(self.hold_times) if len(self.hold_times) > 1 else 0
            ])
        else:
            vector.extend([0, 0, 0])
        
        # DD interval features
        if self.dd_intervals:
            vector.extend([
                statistics.mean(self.dd_intervals),
                statistics.median(self.dd_intervals),
                statistics.stdev(self.dd_intervals) if len(self.dd_intervals) > 1 else 0
            ])
        else:
            vector.extend([0, 0, 0])
        
        # UD interval features
        if self.ud_intervals:
            vector.extend([
                statistics.mean(self.ud_intervals),
                statistics.median(self.ud_intervals),
                statistics.stdev(self.ud_intervals) if len(self.ud_intervals) > 1 else 0
            ])
        else:
            vector.extend([0, 0, 0])
        
        # Typing speed
        vector.append(cps)
        
        # Error rate
        error_rate = self.error_count / self.total_keys if self.total_keys > 0 else 0
        vector.append(error_rate)
        
        # Top N digraph timings
        top_digraphs = self._get_top_digraphs(top_n_digraphs)
        for i in range(top_n_digraphs):
            if i < len(top_digraphs):
                vector.append(top_digraphs[i][1])
            else:
                vector.append(0)
        
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
            avg_timing = statistics.mean(timings)
            digraph_avgs.append((digraph, avg_timing))
        
        # Sort by frequency (number of occurrences)
        digraph_avgs.sort(key=lambda x: len(self.digraph_timings[x[0]]), reverse=True)
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
            avg_timing = statistics.mean(timings)
            trigraph_avgs.append((trigraph, avg_timing))
        
        # Sort by frequency
        trigraph_avgs.sort(key=lambda x: len(self.trigraph_timings[x[0]]), reverse=True)
        return trigraph_avgs[:n]
    
    def reset(self) -> None:
        """Reset all feature data for new session."""
        self.hold_times.clear()
        self.dd_intervals.clear()
        self.ud_intervals.clear()
        self.digraph_timings.clear()
        self.trigraph_timings.clear()
        self.error_count = 0
        self.total_keys = 0
        self.session_start = None
        self.session_end = None
        self._key_down_times.clear()
        self._last_down_time = None
        self._last_up_time = None
        self._key_sequence.clear()


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
