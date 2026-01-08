"""
ShadowKey Phase 2 - Real-time Visualization Module
Live plotting of keystroke features using matplotlib embedded in Tkinter.
"""

import matplotlib
matplotlib.use('TkAgg')  # Set backend before importing pyplot

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import List, Optional
import tkinter as tk
from collections import deque


class LiveVisualizer:
    """
    Manages real-time visualization of keystroke features.
    Embeds matplotlib charts in Tkinter GUI.
    """
    
    def __init__(self, parent_frame: tk.Frame, rolling_window: int = 100):
        """
        Initialize visualizer with parent Tkinter frame.
        
        Args:
            parent_frame: Tkinter frame to embed plots
            rolling_window: Number of recent data points to display
        """
        self.parent_frame = parent_frame
        self.rolling_window = rolling_window
        
        # Data buffers (using deque for efficient rolling window)
        self.hold_times = deque(maxlen=rolling_window)
        self.dd_intervals = deque(maxlen=rolling_window)
        self.ud_intervals = deque(maxlen=rolling_window)
        self.typing_speeds = deque(maxlen=rolling_window)
        self.timestamps = deque(maxlen=rolling_window)
        self.error_counts = []
        
        # Anomaly flag for visual alert
        self.anomaly_detected = False
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 6), dpi=80, facecolor='#f0f0f0')
        self.canvas = None
        self.axes = {}
        
        self._setup_plots()
    
    def _setup_plots(self) -> None:
        """Create subplot layout and initialize charts."""
        # Create 2x2 grid of subplots
        gs = self.fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Hold Time Distribution (top-left)
        self.axes['hold'] = self.fig.add_subplot(gs[0, 0])
        self.axes['hold'].set_title('Hold Time Distribution', fontsize=10, fontweight='bold')
        self.axes['hold'].set_xlabel('Hold Time (s)', fontsize=8)
        self.axes['hold'].set_ylabel('Frequency', fontsize=8)
        self.axes['hold'].tick_params(labelsize=7)
        
        # Flight Time (DD vs UD) (top-right)
        self.axes['flight'] = self.fig.add_subplot(gs[0, 1])
        self.axes['flight'].set_title('Flight Time (DD vs UD)', fontsize=10, fontweight='bold')
        self.axes['flight'].set_xlabel('Event #', fontsize=8)
        self.axes['flight'].set_ylabel('Interval (s)', fontsize=8)
        self.axes['flight'].tick_params(labelsize=7)
        
        # Typing Speed (bottom-left)
        self.axes['speed'] = self.fig.add_subplot(gs[1, 0])
        self.axes['speed'].set_title('Typing Speed Over Time', fontsize=10, fontweight='bold')
        self.axes['speed'].set_xlabel('Time (s)', fontsize=8)
        self.axes['speed'].set_ylabel('Speed (CPS)', fontsize=8)
        self.axes['speed'].tick_params(labelsize=7)
        
        # Error Count (bottom-right)
        self.axes['errors'] = self.fig.add_subplot(gs[1, 1])
        self.axes['errors'].set_title('Error Count Progress', fontsize=10, fontweight='bold')
        self.axes['errors'].set_xlabel('Session Progress', fontsize=8)
        self.axes['errors'].set_ylabel('Cumulative Errors', fontsize=8)
        self.axes['errors'].tick_params(labelsize=7)
        
        # Create canvas and embed in parent frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_hold_times(self, new_hold_times: List[float]) -> None:
        """
        Update hold time histogram.
        
        Args:
            new_hold_times: List of new hold time values
        """
        self.hold_times.extend(new_hold_times)
        
        if len(self.hold_times) < 5:
            return
        
        ax = self.axes['hold']
        ax.clear()
        
        # Create histogram
        color = '#ff6b6b' if self.anomaly_detected else '#4ecdc4'
        ax.hist(list(self.hold_times), bins=15, color=color, alpha=0.7, edgecolor='black')
        
        ax.set_title('Hold Time Distribution', fontsize=10, fontweight='bold')
        ax.set_xlabel('Hold Time (s)', fontsize=8)
        ax.set_ylabel('Frequency', fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.3)
    
    def update_flight_times(self, new_dd: List[float], new_ud: List[float]) -> None:
        """
        Update flight time line chart (DD and UD intervals).
        
        Args:
            new_dd: New down-down intervals
            new_ud: New up-down intervals
        """
        self.dd_intervals.extend(new_dd)
        self.ud_intervals.extend(new_ud)
        
        if len(self.dd_intervals) < 2:
            return
        
        ax = self.axes['flight']
        ax.clear()
        
        # Plot DD and UD as separate lines
        x_dd = list(range(len(self.dd_intervals)))
        x_ud = list(range(len(self.ud_intervals)))
        
        color_dd = '#ff6b6b' if self.anomaly_detected else '#4ecdc4'
        color_ud = '#ff9999' if self.anomaly_detected else '#95e1d3'
        
        if x_dd:
            ax.plot(x_dd, list(self.dd_intervals), label='Down-Down', 
                   color=color_dd, linewidth=2, marker='o', markersize=3)
        
        if x_ud:
            ax.plot(x_ud, list(self.ud_intervals), label='Up-Down',
                   color=color_ud, linewidth=2, marker='s', markersize=3, alpha=0.7)
        
        ax.set_title('Flight Time (DD vs UD)', fontsize=10, fontweight='bold')
        ax.set_xlabel('Event #', fontsize=8)
        ax.set_ylabel('Interval (s)', fontsize=8)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=7, loc='upper right')
        ax.grid(True, alpha=0.3)
    
    def update_typing_speed(self, timestamp: float, speed_cps: float) -> None:
        """
        Update typing speed chart.
        
        Args:
            timestamp: Current timestamp
            speed_cps: Current typing speed in characters per second
        """
        self.timestamps.append(timestamp)
        self.typing_speeds.append(speed_cps)
        
        if len(self.typing_speeds) < 2:
            return
        
        ax = self.axes['speed']
        ax.clear()
        
        # Convert timestamps to relative seconds
        times = np.array(list(self.timestamps))
        times = times - times[0]  # Start from 0
        speeds = list(self.typing_speeds)
        
        color = '#ff6b6b' if self.anomaly_detected else '#45b7d1'
        ax.plot(times, speeds, color=color, linewidth=2.5)
        ax.fill_between(times, speeds, alpha=0.3, color=color)
        
        ax.set_title('Typing Speed Over Time', fontsize=10, fontweight='bold')
        ax.set_xlabel('Time (s)', fontsize=8)
        ax.set_ylabel('Speed (CPS)', fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.3)
        
        # Add average line
        avg_speed = np.mean(speeds)
        ax.axhline(y=avg_speed, color='gray', linestyle='--', linewidth=1, alpha=0.7)
        ax.text(0.02, 0.98, f'Avg: {avg_speed:.2f} CPS', 
               transform=ax.transAxes, fontsize=7, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def update_error_count(self, current_errors: int, total_keys: int) -> None:
        """
        Update error count display.
        
        Args:
            current_errors: Current cumulative error count
            total_keys: Total keys typed so far
        """
        self.error_counts.append(current_errors)
        
        ax = self.axes['errors']
        ax.clear()
        
        if len(self.error_counts) > 1:
            color = '#ff6b6b' if self.anomaly_detected else '#f38181'
            ax.plot(self.error_counts, color=color, linewidth=3, marker='o', markersize=4)
            ax.fill_between(range(len(self.error_counts)), self.error_counts, 
                           alpha=0.3, color=color)
        else:
            ax.bar([0], [current_errors], color='#f38181', alpha=0.7)
        
        ax.set_title('Error Count Progress', fontsize=10, fontweight='bold')
        ax.set_xlabel('Session Progress', fontsize=8)
        ax.set_ylabel('Cumulative Errors', fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Show error rate
        error_rate = (current_errors / total_keys * 100) if total_keys > 0 else 0
        ax.text(0.98, 0.98, f'Error Rate: {error_rate:.1f}%', 
               transform=ax.transAxes, fontsize=7, verticalalignment='top',
               horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def mark_anomaly(self, is_anomaly: bool) -> None:
        """
        Mark anomaly detection status for visual feedback.
        
        Args:
            is_anomaly: Whether current pattern is anomalous
        """
        self.anomaly_detected = is_anomaly
        
        # Change figure background color to indicate anomaly
        if is_anomaly:
            self.fig.patch.set_facecolor('#ffe6e6')  # Light red
        else:
            self.fig.patch.set_facecolor('#f0f0f0')  # Normal gray
    
    def refresh_canvas(self) -> None:
        """Redraw the matplotlib canvas."""
        if self.canvas:
            self.canvas.draw()
            self.canvas.flush_events()
    
    def clear_all(self) -> None:
        """Reset all visualizations for new session."""
        self.hold_times.clear()
        self.dd_intervals.clear()
        self.ud_intervals.clear()
        self.typing_speeds.clear()
        self.timestamps.clear()
        self.error_counts.clear()
        self.anomaly_detected = False
        
        # Clear all axes
        for ax in self.axes.values():
            ax.clear()
        
        self.fig.patch.set_facecolor('#f0f0f0')
        self.refresh_canvas()


# Example usage (requires Tkinter window)
if __name__ == "__main__":
    print("LiveVisualizer requires Tkinter integration")
    print("Run shadowkey_phase2.py to see visualization in action")
