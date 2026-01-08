"""
ShadowKey Phase 1 - Main Application
A desktop application for capturing keystroke timing data and extracting typing behavior features.

Features:
- Real-time keystroke capture with key down/up timestamps
- Typing behavior feature extraction
- Session-based data storage
- Export to JSON

Author: ShadowKey Development Team
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
import json
import os

from keystroke_capture import KeystrokeCapture
from feature_extractor import FeatureExtractor
from data_storage import DataStorage


class ShadowKeyApp:
    """
    Main application class for ShadowKey keystroke capture and analysis.
    """
    
    def __init__(self, root):
        """
        Initialize the ShadowKey application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("ShadowKey - Keystroke Behavior Analysis")
        self.root.geometry("900x700")
        self.root.configure(bg='#1e1e2e')
        
        # Initialize components
        self.capture = KeystrokeCapture()
        self.storage = DataStorage()
        self.current_session_id = None
        self.user_id = "default_user"
        
        # Session state
        self.is_session_active = False
        
        # Load configuration
        self.load_config()
        
        # Setup UI
        self.setup_ui()
        
        # Bind capture to text widget
        self.capture.bind_to_widget(self.text_input)
        
        # Setup update loop for statistics
        self.update_statistics()
        
    def load_config(self):
        """Load configuration from config.json if it exists."""
        config_file = "config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.user_id = config.get('user_id', 'default_user')
            except Exception as e:
                print(f"Error loading config: {e}")
                
    def setup_ui(self):
        """Setup the user interface components."""
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TFrame', background='#1e1e2e')
        style.configure('TLabel', background='#1e1e2e', foreground='#cdd6f4', font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#89b4fa')
        style.configure('Stats.TLabel', font=('Segoe UI', 11), foreground='#a6e3a1')
        style.configure('TButton', font=('Segoe UI', 10, 'bold'))
        
        # Header
        header_frame = ttk.Frame(self.root, style='TFrame')
        header_frame.pack(fill=tk.X, padx=20, pady=15)
        
        title_label = ttk.Label(
            header_frame, 
            text="🔑 ShadowKey - Keystroke Behavior Analysis", 
            style='Header.TLabel'
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Real-time typing pattern capture and feature extraction",
            style='TLabel'
        )
        subtitle_label.pack()
        
        # Control Panel
        control_frame = ttk.Frame(self.root, style='TFrame')
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Session controls
        self.start_button = tk.Button(
            control_frame,
            text="▶ Start Capture",
            command=self.start_session,
            bg='#a6e3a1',
            fg='#1e1e2e',
            font=('Segoe UI', 11, 'bold'),
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(
            control_frame,
            text="⏸ Stop & Save",
            command=self.stop_session,
            bg='#f38ba8',
            fg='#1e1e2e',
            font=('Segoe UI', 11, 'bold'),
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.export_button = tk.Button(
            control_frame,
            text="📤 Export to JSON",
            command=self.export_session,
            bg='#89b4fa',
            fg='#1e1e2e',
            font=('Segoe UI', 11, 'bold'),
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        # Statistics Panel
        stats_frame = ttk.Frame(self.root, style='TFrame')
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        stats_title = ttk.Label(stats_frame, text="📊 Session Statistics", style='Header.TLabel', font=('Segoe UI', 12, 'bold'))
        stats_title.pack(anchor=tk.W)
        
        # Stats grid
        stats_grid = ttk.Frame(stats_frame, style='TFrame')
        stats_grid.pack(fill=tk.X, pady=10)
        
        # Session status
        self.status_label = ttk.Label(stats_grid, text="Status: Idle", style='Stats.TLabel')
        self.status_label.grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Session timestamp
        self.timestamp_label = ttk.Label(stats_grid, text="Session Start: N/A", style='TLabel')
        self.timestamp_label.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Total keys
        self.keys_label = ttk.Label(stats_grid, text="Total Keys: 0", style='Stats.TLabel')
        self.keys_label.grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Typing speed
        self.speed_label = ttk.Label(stats_grid, text="Typing Speed: 0.0 CPS", style='TLabel')
        self.speed_label.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Session duration
        self.duration_label = ttk.Label(stats_grid, text="Duration: 0s", style='TLabel')
        self.duration_label.grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Text Input Area
        input_frame = ttk.Frame(self.root, style='TFrame')
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        input_label = ttk.Label(input_frame, text="✍ Type here to capture keystrokes:", style='TLabel', font=('Segoe UI', 11, 'bold'))
        input_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.text_input = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=('Consolas', 11),
            bg='#313244',
            fg='#cdd6f4',
            insertbackground='#89b4fa',
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.text_input.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder text
        placeholder_text = "Click 'Start Capture' and begin typing to record keystroke timing data...\n\nThis application captures:\n• Key down/up timestamps\n• Hold times and flight times\n• Digraph and trigraph patterns\n• Typing speed and error rates\n\nAll data is stored securely in a local SQLite database."
        self.text_input.insert('1.0', placeholder_text)
        self.text_input.config(state=tk.DISABLED)
        
        # Footer
        footer_frame = ttk.Frame(self.root, style='TFrame')
        footer_frame.pack(fill=tk.X, padx=20, pady=10)
        
        footer_label = ttk.Label(
            footer_frame,
            text=f"User: {self.user_id} | Database: shadowkey_data.db",
            style='TLabel',
            font=('Segoe UI', 9)
        )
        footer_label.pack()
        
    def start_session(self):
        """Start a new keystroke capture session."""
        # Enable text input
        self.text_input.config(state=tk.NORMAL)
        self.text_input.delete('1.0', tk.END)
        
        # Start capture
        self.capture.start_capture()
        self.is_session_active = True
        
        # Create session in database
        self.current_session_id = self.storage.create_session(
            self.user_id,
            self.capture.session_start_time
        )
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: 🔴 Recording", foreground='#f38ba8')
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.timestamp_label.config(text=f"Session Start: {timestamp}")
        
        self.text_input.focus()
        
    def stop_session(self):
        """Stop the current session and save data."""
        if not self.is_session_active:
            return
            
        # Stop capture
        self.capture.stop_capture()
        self.is_session_active = False
        
        # Get events
        events = self.capture.get_events()
        
        if len(events) == 0:
            messagebox.showwarning("No Data", "No keystrokes were captured in this session.")
            self.reset_ui()
            return
        
        # Extract features
        extractor = FeatureExtractor(events)
        features = extractor.extract_all_features()
        
        # Store in database
        import time
        self.storage.update_session(
            self.current_session_id,
            time.time(),
            self.capture.get_key_count()
        )
        self.storage.store_keystrokes(self.current_session_id, events)
        self.storage.store_features(self.current_session_id, features)
        
        # Update UI
        self.text_input.config(state=tk.DISABLED)
        self.status_label.config(text="Status: ✅ Saved", foreground='#a6e3a1')
        
        # Show summary
        messagebox.showinfo(
            "Session Saved",
            f"Session #{self.current_session_id} saved successfully!\n\n"
            f"Total Keys: {features['total_keys']}\n"
            f"Duration: {features['session_duration']}s\n"
            f"Typing Speed: {features['typing_speed']['characters_per_second']} CPS\n"
            f"Errors: {features['error_count']['total_errors']}"
        )
        
        self.reset_ui()
        
    def export_session(self):
        """Export the last session to JSON file."""
        if self.current_session_id is None:
            # Get the most recent session
            sessions = self.storage.get_all_sessions(self.user_id)
            if not sessions:
                messagebox.showwarning("No Sessions", "No sessions available to export.")
                return
            self.current_session_id = sessions[0]['session_id']
        
        # Ask user for save location
        default_filename = f"shadowkey_session_{self.current_session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if file_path:
            try:
                self.storage.export_session_to_json(self.current_session_id, file_path)
                messagebox.showinfo("Export Success", f"Session exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export session:\n{str(e)}")
                
    def reset_ui(self):
        """Reset UI to initial state."""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.keys_label.config(text="Total Keys: 0")
        self.speed_label.config(text="Typing Speed: 0.0 CPS")
        self.duration_label.config(text="Duration: 0s")
        
    def update_statistics(self):
        """Update real-time statistics display."""
        if self.is_session_active:
            key_count = self.capture.get_key_count()
            self.keys_label.config(text=f"Total Keys: {key_count}")
            
            # Calculate duration
            if self.capture.session_start_time:
                import time
                duration = time.time() - self.capture.session_start_time
                self.duration_label.config(text=f"Duration: {int(duration)}s")
                
                # Calculate speed
                if duration > 0:
                    cps = key_count / duration
                    self.speed_label.config(text=f"Typing Speed: {cps:.1f} CPS")
        
        # Schedule next update
        self.root.after(500, self.update_statistics)
        
    def on_closing(self):
        """Handle window close event."""
        if self.is_session_active:
            result = messagebox.askyesnocancel(
                "Session Active",
                "A session is currently active. Do you want to save it before closing?"
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes
                self.stop_session()
        
        self.storage.close()
        self.root.destroy()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = ShadowKeyApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
