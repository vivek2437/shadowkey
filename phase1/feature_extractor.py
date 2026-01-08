"""
Feature Extraction Module for ShadowKey Phase 1

This module analyzes keystroke events and extracts typing behavior features
including hold times, flight times, digraphs, trigraphs, typing speed, and errors.
"""

from typing import List, Dict, Tuple
import statistics
from keystroke_capture import KeystrokeEvent


class FeatureExtractor:
    """
    Extracts typing behavior features from keystroke events.
    
    Features include:
    - Key hold times (duration between key down and key up)
    - Flight times (DD: down-down, UD: up-down intervals)
    - Digraph timing patterns (2-character sequences)
    - Trigraph timing patterns (3-character sequences)
    - Typing speed (characters per second)
    - Error count (backspace/delete usage)
    """
    
    def __init__(self, events: List[KeystrokeEvent]):
        """
        Initialize feature extractor with keystroke events.
        
        Args:
            events: List of KeystrokeEvent objects to analyze
        """
        self.events = events
        self.features = {}
        
    def extract_all_features(self) -> Dict:
        """
        Extract all typing behavior features from the events.
        
        Returns:
            Dictionary containing all extracted features
        """
        self.features = {
            'hold_times': self.calculate_hold_times(),
            'flight_times': self.calculate_flight_times(),
            'digraphs': self.extract_digraphs(),
            'trigraphs': self.extract_trigraphs(),
            'typing_speed': self.calculate_typing_speed(),
            'error_count': self.count_errors(),
            'total_keys': self.get_total_keys(),
            'session_duration': self.get_session_duration()
        }
        return self.features
        
    def calculate_hold_times(self) -> Dict:
        """
        Calculate hold time for each key (time between key down and key up).
        
        Returns:
            Dictionary with hold time statistics and individual measurements
        """
        hold_times = []
        key_hold_map = {}  # Map to track down events waiting for up events
        
        for event in self.events:
            key_id = f"{event.key}_{event.key_code}"
            
            if event.event_type == 'down':
                # Store the down event timestamp
                key_hold_map[key_id] = event.timestamp
            elif event.event_type == 'up' and key_id in key_hold_map:
                # Calculate hold time
                hold_time = event.timestamp - key_hold_map[key_id]
                hold_times.append({
                    'key': event.key,
                    'hold_time_ms': hold_time * 1000  # Convert to milliseconds
                })
                del key_hold_map[key_id]
        
        # Calculate statistics
        if hold_times:
            times = [h['hold_time_ms'] for h in hold_times]
            return {
                'measurements': hold_times,
                'count': len(hold_times),
                'mean_ms': statistics.mean(times),
                'median_ms': statistics.median(times),
                'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0,
                'min_ms': min(times),
                'max_ms': max(times)
            }
        return {'measurements': [], 'count': 0}
        
    def calculate_flight_times(self) -> Dict:
        """
        Calculate flight times between consecutive key presses.
        DD: Down-Down interval (time between consecutive key presses)
        UD: Up-Down interval (time from key release to next key press)
        
        Returns:
            Dictionary with DD and UD flight time statistics
        """
        down_events = [e for e in self.events if e.event_type == 'down']
        up_events = [e for e in self.events if e.event_type == 'up']
        
        # Calculate DD (Down-Down) intervals
        dd_times = []
        for i in range(len(down_events) - 1):
            dd_interval = (down_events[i + 1].timestamp - down_events[i].timestamp) * 1000
            dd_times.append({
                'from_key': down_events[i].key,
                'to_key': down_events[i + 1].key,
                'interval_ms': dd_interval
            })
        
        # Calculate UD (Up-Down) intervals
        ud_times = []
        for i in range(len(up_events)):
            # Find the next down event after this up event
            for down_event in down_events:
                if down_event.timestamp > up_events[i].timestamp:
                    ud_interval = (down_event.timestamp - up_events[i].timestamp) * 1000
                    ud_times.append({
                        'from_key': up_events[i].key,
                        'to_key': down_event.key,
                        'interval_ms': ud_interval
                    })
                    break
        
        # Calculate statistics for DD
        dd_stats = {}
        if dd_times:
            dd_values = [t['interval_ms'] for t in dd_times]
            dd_stats = {
                'measurements': dd_times,
                'count': len(dd_times),
                'mean_ms': statistics.mean(dd_values),
                'median_ms': statistics.median(dd_values),
                'std_dev_ms': statistics.stdev(dd_values) if len(dd_values) > 1 else 0
            }
        else:
            dd_stats = {'measurements': [], 'count': 0}
            
        # Calculate statistics for UD
        ud_stats = {}
        if ud_times:
            ud_values = [t['interval_ms'] for t in ud_times]
            ud_stats = {
                'measurements': ud_times,
                'count': len(ud_times),
                'mean_ms': statistics.mean(ud_values),
                'median_ms': statistics.median(ud_values),
                'std_dev_ms': statistics.stdev(ud_values) if len(ud_values) > 1 else 0
            }
        else:
            ud_stats = {'measurements': [], 'count': 0}
        
        return {
            'down_down': dd_stats,
            'up_down': ud_stats
        }
        
    def extract_digraphs(self) -> Dict:
        """
        Extract timing patterns for 2-character sequences (digraphs).
        
        Returns:
            Dictionary of digraph patterns with timing data
        """
        down_events = [e for e in self.events if e.event_type == 'down']
        digraphs = []
        
        for i in range(len(down_events) - 1):
            digraph = down_events[i].key + down_events[i + 1].key
            interval = (down_events[i + 1].timestamp - down_events[i].timestamp) * 1000
            
            digraphs.append({
                'digraph': digraph,
                'interval_ms': interval
            })
        
        return {
            'measurements': digraphs,
            'count': len(digraphs),
            'unique_digraphs': len(set(d['digraph'] for d in digraphs))
        }
        
    def extract_trigraphs(self) -> Dict:
        """
        Extract timing patterns for 3-character sequences (trigraphs).
        
        Returns:
            Dictionary of trigraph patterns with timing data
        """
        down_events = [e for e in self.events if e.event_type == 'down']
        trigraphs = []
        
        for i in range(len(down_events) - 2):
            trigraph = down_events[i].key + down_events[i + 1].key + down_events[i + 2].key
            # Calculate average interval across the three keys
            interval1 = (down_events[i + 1].timestamp - down_events[i].timestamp) * 1000
            interval2 = (down_events[i + 2].timestamp - down_events[i + 1].timestamp) * 1000
            avg_interval = (interval1 + interval2) / 2
            
            trigraphs.append({
                'trigraph': trigraph,
                'avg_interval_ms': avg_interval,
                'total_duration_ms': interval1 + interval2
            })
        
        return {
            'measurements': trigraphs,
            'count': len(trigraphs),
            'unique_trigraphs': len(set(t['trigraph'] for t in trigraphs))
        }
        
    def calculate_typing_speed(self) -> Dict:
        """
        Calculate typing speed in characters per second and words per minute.
        
        Returns:
            Dictionary with typing speed metrics
        """
        down_events = [e for e in self.events if e.event_type == 'down']
        
        if len(down_events) < 2:
            return {
                'characters_per_second': 0,
                'words_per_minute': 0,
                'total_characters': 0
            }
        
        # Calculate session duration
        session_duration = down_events[-1].timestamp - down_events[0].timestamp
        
        if session_duration == 0:
            return {
                'characters_per_second': 0,
                'words_per_minute': 0,
                'total_characters': len(down_events)
            }
        
        # Calculate characters per second
        cps = len(down_events) / session_duration
        
        # Calculate words per minute (assuming 5 characters per word on average)
        wpm = (len(down_events) / 5) / (session_duration / 60)
        
        return {
            'characters_per_second': round(cps, 2),
            'words_per_minute': round(wpm, 2),
            'total_characters': len(down_events),
            'session_duration_seconds': round(session_duration, 2)
        }
        
    def count_errors(self) -> Dict:
        """
        Count error corrections (backspace and delete key usage).
        
        Returns:
            Dictionary with error count metrics
        """
        backspace_count = 0
        delete_count = 0
        
        for event in self.events:
            if event.event_type == 'down':
                if event.key in ['BackSpace', '\x08']:
                    backspace_count += 1
                elif event.key in ['Delete', '\x7f']:
                    delete_count += 1
        
        total_errors = backspace_count + delete_count
        total_keys = self.get_total_keys()
        error_rate = (total_errors / total_keys * 100) if total_keys > 0 else 0
        
        return {
            'backspace_count': backspace_count,
            'delete_count': delete_count,
            'total_errors': total_errors,
            'error_rate_percent': round(error_rate, 2)
        }
        
    def get_total_keys(self) -> int:
        """
        Get total number of key presses (down events).
        
        Returns:
            Integer count of key presses
        """
        return sum(1 for e in self.events if e.event_type == 'down')
        
    def get_session_duration(self) -> float:
        """
        Get total session duration in seconds.
        
        Returns:
            Float representing session duration
        """
        if not self.events:
            return 0.0
            
        start_time = min(e.timestamp for e in self.events)
        end_time = max(e.timestamp for e in self.events)
        
        return round(end_time - start_time, 2)
