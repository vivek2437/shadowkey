"""
ShadowKey Phase 2 - System-wide Keystroke Capture Module
Global keystroke capture using pynput library with thread-safe event handling.
"""

import time
import queue
import threading
from dataclasses import dataclass
from typing import Optional, List
from pynput import keyboard


@dataclass
class KeystrokeEvent:
    """Represents a single keystroke event with microsecond precision."""
    key: str
    event_type: str  # 'down' or 'up'
    timestamp: float  # High-precision timestamp
    
    def __repr__(self) -> str:
        return f"KeystrokeEvent(key={self.key}, type={self.event_type}, ts={self.timestamp:.6f})"


class SystemCaptureManager:
    """
    Manages system-wide keystroke capture using pynput.
    Provides thread-safe event queue for downstream processing.
    """
    
    def __init__(self):
        """Initialize capture manager with empty event queue."""
        self.event_queue: queue.Queue = queue.Queue()
        self.listener: Optional[keyboard.Listener] = None
        self.is_capturing: bool = False
        self._lock = threading.Lock()
    
    def _normalize_key(self, key) -> str:
        """
        Normalize pynput key object to string representation.
        
        Args:
            key: pynput key object
            
        Returns:
            String representation of key
        """
        try:
            # Handle alphanumeric keys
            if hasattr(key, 'char') and key.char is not None:
                return key.char
            
            # Handle special keys
            if hasattr(key, 'name'):
                return f"[{key.name}]"
            
            # Fallback
            return str(key).replace("Key.", "[").replace("'", "") + "]"
        
        except Exception:
            return "[unknown]"
    
    def _on_press(self, key) -> None:
        """
        Callback for key press events.
        
        Args:
            key: pynput key object
        """
        if not self.is_capturing:
            return
        
        try:
            key_str = self._normalize_key(key)
            timestamp = time.time()  # High-precision timestamp
            
            event = KeystrokeEvent(
                key=key_str,
                event_type='down',
                timestamp=timestamp
            )
            
            self.event_queue.put(event)
        
        except Exception as e:
            print(f"Error in on_press: {e}")
    
    def _on_release(self, key) -> None:
        """
        Callback for key release events.
        
        Args:
            key: pynput key object
        """
        if not self.is_capturing:
            return
        
        try:
            key_str = self._normalize_key(key)
            timestamp = time.time()
            
            event = KeystrokeEvent(
                key=key_str,
                event_type='up',
                timestamp=timestamp
            )
            
            self.event_queue.put(event)
        
        except Exception as e:
            print(f"Error in on_release: {e}")
    
    def start_capture(self) -> None:
        """
        Start system-wide keystroke capture.
        Launches pynput listener in background thread.
        """
        with self._lock:
            if self.is_capturing:
                print("Capture already running")
                return
            
            self.is_capturing = True
            
            # Create and start listener
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.start()
            
            print("System-wide capture started")
    
    def stop_capture(self) -> None:
        """
        Stop keystroke capture gracefully.
        Stops listener and clears remaining events.
        """
        with self._lock:
            if not self.is_capturing:
                return
            
            self.is_capturing = False
            
            if self.listener:
                self.listener.stop()
                self.listener = None
            
            print("System-wide capture stopped")
    
    def get_events(self, max_events: int = 100) -> List[KeystrokeEvent]:
        """
        Thread-safe retrieval of captured events.
        
        Args:
            max_events: Maximum number of events to retrieve
            
        Returns:
            List of KeystrokeEvent objects
        """
        events = []
        
        try:
            while len(events) < max_events:
                event = self.event_queue.get_nowait()
                events.append(event)
        except queue.Empty:
            pass
        
        return events
    
    def has_events(self) -> bool:
        """
        Check if there are events in the queue.
        
        Returns:
            True if events are available
        """
        return not self.event_queue.empty()
    
    def clear_events(self) -> None:
        """Clear all pending events from queue."""
        while not self.event_queue.empty():
            try:
                self.event_queue.get_nowait()
            except queue.Empty:
                break


# Example usage
if __name__ == "__main__":
    print("Testing System Capture Manager")
    print("Type some keys (will capture for 10 seconds)...")
    
    manager = SystemCaptureManager()
    manager.start_capture()
    
    # Capture for 10 seconds
    time.sleep(10)
    
    manager.stop_capture()
    
    # Get and display events
    events = manager.get_events()
    print(f"\nCaptured {len(events)} events:")
    for event in events[:20]:  # Show first 20
        print(event)
