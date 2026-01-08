"""
Keystroke Capture Module for ShadowKey Phase 1

This module provides functionality to capture and record keystroke events
including key down and key up events with precise timestamps.
"""

from dataclasses import dataclass
from typing import List
import time


@dataclass
class KeystrokeEvent:
    """
    Represents a single keystroke event.
    
    Attributes:
        key: The key that was pressed (character or key name)
        timestamp: Unix timestamp (seconds) when the event occurred
        event_type: Type of event ('down' or 'up')
        key_code: Tkinter keycode for the event
    """
    key: str
    timestamp: float
    event_type: str  # 'down' or 'up'
    key_code: int


class KeystrokeCapture:
    """
    Manages keystroke event capture for a Tkinter text widget.
    
    This class binds to key press and release events, records timing data,
    and maintains a session-based collection of keystroke events.
    """
    
    def __init__(self):
        """Initialize the keystroke capture system."""
        self.events: List[KeystrokeEvent] = []
        self.is_capturing = False
        self.session_start_time = None
        
    def start_capture(self):
        """Begin capturing keystroke events."""
        self.is_capturing = True
        self.session_start_time = time.time()
        self.events.clear()
        
    def stop_capture(self):
        """Stop capturing keystroke events."""
        self.is_capturing = False
        
    def on_key_press(self, event) -> str:
        """
        Handle key press (key down) event.
        
        Args:
            event: Tkinter key event object
            
        Returns:
            String to allow event propagation
        """
        if self.is_capturing:
            # Record the key down event
            keystroke = KeystrokeEvent(
                key=event.char if event.char else event.keysym,
                timestamp=time.time(),
                event_type='down',
                key_code=event.keycode
            )
            self.events.append(keystroke)
        
        # Return None to allow normal event processing
        return None
        
    def on_key_release(self, event) -> str:
        """
        Handle key release (key up) event.
        
        Args:
            event: Tkinter key event object
            
        Returns:
            String to allow event propagation
        """
        if self.is_capturing:
            # Record the key up event
            keystroke = KeystrokeEvent(
                key=event.char if event.char else event.keysym,
                timestamp=time.time(),
                event_type='up',
                key_code=event.keycode
            )
            self.events.append(keystroke)
        
        # Return None to allow normal event processing
        return None
        
    def bind_to_widget(self, widget):
        """
        Bind keystroke capture to a Tkinter widget.
        
        Args:
            widget: Tkinter widget (typically Text widget) to monitor
        """
        # Bind to both key press and key release events
        widget.bind('<KeyPress>', self.on_key_press)
        widget.bind('<KeyRelease>', self.on_key_release)
        
    def get_events(self) -> List[KeystrokeEvent]:
        """
        Get all captured keystroke events for the current session.
        
        Returns:
            List of KeystrokeEvent objects
        """
        return self.events.copy()
        
    def get_event_count(self) -> int:
        """
        Get the total number of events captured.
        
        Returns:
            Integer count of events
        """
        return len(self.events)
        
    def get_key_count(self) -> int:
        """
        Get the count of actual key presses (down events only).
        
        Returns:
            Integer count of key press events
        """
        return sum(1 for event in self.events if event.event_type == 'down')
        
    def clear_events(self):
        """Clear all captured events."""
        self.events.clear()
        self.session_start_time = None
