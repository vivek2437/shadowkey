"""
ShadowKey Phase 2 - Main Application
System-wide keystroke capture with ML authentication and real-time visualization.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
from pathlib import Path
from typing import Optional

# Import local modules
from system_capture import SystemCaptureManager, KeystrokeEvent
from feature_extractor import FeatureExtractor, KeyEvent
from ml_auth import BehavioralAuthenticator
from data_storage import DataStorage
from visualization import LiveVisualizer


class ShadowKeyApp:
    """Main application class for ShadowKey Phase 2."""
    
    def __init__(self, root: tk.Tk, config_path: str = "config_phase2.json"):
        """
        Initialize application.
        
        Args:
            root: Tkinter root window
            config_path: Path to configuration file
        """
        self.root = root
        self.root.title("ShadowKey Phase 2 - ML Keystroke Authentication")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.capture_manager = SystemCaptureManager()
        self.feature_extractor = FeatureExtractor()
        self.authenticator = BehavioralAuthenticator(
            model_path=self.config['ml']['model_path'],
            scaler_path=self.config['ml']['scaler_path'],
            contamination=self.config['ml']['contamination']
        )
        self.db = DataStorage(self.config['database']['path'])
        
        # Session state
        self.current_user_id: Optional[int] = None
        self.current_session_id: Optional[int] = None
        self.is_session_active: bool = False
        self.processing_thread: Optional[threading.Thread] = None
        self.should_stop_processing: bool = False
        
        # Statistics
        self.keys_typed: int = 0
        self.update_counter: int = 0
        self.last_prediction_time: float = 0
        
        # Try to load existing model
        self.authenticator.load_model()
        
        # Build GUI
        self._create_menu()
        self._create_widgets()
        
        # Set up user
        self._setup_default_user()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Use default config
            return {
                'database': {'path': 'shadowkey_data.db'},
                'ml': {
                    'model_path': 'models/behavioral_auth.pkl',
                    'scaler_path': 'models/feature_scaler.pkl',
                    'contamination': 0.05,
                    'prediction_interval': 50
                },
                'visualization': {'update_interval': 10},
                'export': {'json_dir': 'exports/json', 'csv_dir': 'exports/csv'}
            }
    
    def _setup_default_user(self) -> None:
        """Set up default user for the application."""
        username = "default_user"
        self.current_user_id = self.db.create_user(username)
        self.user_label.config(text=f"User: {username}")
    
    def _create_menu(self) -> None:
        """Create application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Last Session (JSON)", command=self._export_json)
        file_menu.add_command(label="Export Last Session (CSV)", command=self._export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # ML menu
        ml_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ML Model", menu=ml_menu)
        ml_menu.add_command(label="Train Model", command=self._train_model)
        ml_menu.add_command(label="View Model Info", command=self._show_model_info)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_widgets(self) -> None:
        """Create main GUI widgets."""
        # Top control panel
        control_frame = tk.Frame(self.root, bg='#34495e', pady=10)
        control_frame.pack(fill=tk.X)
        
        # Buttons
        self.start_btn = tk.Button(
            control_frame, text="▶ Start Session", command=self._start_session,
            bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
            padx=20, pady=10, relief=tk.RAISED
        )
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(
            control_frame, text="⬛ Stop Session", command=self._stop_session,
            bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
            padx=20, pady=10, relief=tk.RAISED, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        self.train_btn = tk.Button(
            control_frame, text="🧠 Train ML Model", command=self._train_model,
            bg='#3498db', fg='white', font=('Arial', 11, 'bold'),
            padx=15, pady=10, relief=tk.RAISED
        )
        self.train_btn.pack(side=tk.LEFT, padx=10)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg='#2c3e50')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Statistics
        stats_frame = tk.LabelFrame(
            content_frame, text="Session Statistics", 
            bg='#ecf0f1', fg='#2c3e50', font=('Arial', 11, 'bold'),
            padx=15, pady=15
        )
        stats_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Statistics labels
        self.user_label = tk.Label(
            stats_frame, text="User: Not Set", bg='#ecf0f1',
            font=('Arial', 10), anchor='w'
        )
        self.user_label.pack(fill=tk.X, pady=5)
        
        self.keys_label = tk.Label(
            stats_frame, text="Keys Typed: 0", bg='#ecf0f1',
            font=('Arial', 10), anchor='w'
        )
        self.keys_label.pack(fill=tk.X, pady=5)
        
        self.speed_label = tk.Label(
            stats_frame, text="Speed: 0.0 CPS", bg='#ecf0f1',
            font=('Arial', 10), anchor='w'
        )
        self.speed_label.pack(fill=tk.X, pady=5)
        
        self.wpm_label = tk.Label(
            stats_frame, text="WPM: 0.0", bg='#ecf0f1',
            font=('Arial', 10), anchor='w'
        )
        self.wpm_label.pack(fill=tk.X, pady=5)
        
        self.errors_label = tk.Label(
            stats_frame, text="Errors: 0", bg='#ecf0f1',
            font=('Arial', 10), anchor='w'
        )
        self.errors_label.pack(fill=tk.X, pady=5)
        
        tk.Label(stats_frame, text="", bg='#ecf0f1').pack(pady=10)  # Spacer
        
        # ML Status
        ml_status_frame = tk.Frame(stats_frame, bg='#ecf0f1')
        ml_status_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            ml_status_frame, text="ML Authentication:", bg='#ecf0f1',
            font=('Arial', 10, 'bold')
        ).pack(anchor='w')
        
        self.ml_status_label = tk.Label(
            ml_status_frame, text="⚪ MONITORING", bg='#ecf0f1',
            font=('Arial', 11, 'bold'), fg='#95a5a6'
        )
        self.ml_status_label.pack(fill=tk.X, pady=5)
        
        self.confidence_label = tk.Label(
            ml_status_frame, text="Confidence: --", bg='#ecf0f1',
            font=('Arial', 9)
        )
        self.confidence_label.pack(fill=tk.X, pady=2)
        
        # Right panel - Visualization
        viz_frame = tk.LabelFrame(
            content_frame, text="Real-time Feature Visualization",
            bg='#ecf0f1', fg='#2c3e50', font=('Arial', 11, 'bold'),
            padx=10, pady=10
        )
        viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create visualizer
        self.visualizer = LiveVisualizer(
            viz_frame, 
            rolling_window=self.config['visualization'].get('rolling_window_size', 100)
        )
        
        # Status bar
        self.status_bar = tk.Label(
            self.root, text="Ready", bg='#34495e', fg='white',
            font=('Arial', 9), anchor='w', padx=10
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _start_session(self) -> None:
        """Start a new keystroke capture session."""
        if self.is_session_active:
            return
        
        # Reset feature extractor
        self.feature_extractor.reset()
        self.keys_typed = 0
        self.update_counter = 0
        self.last_prediction_time = time.time()
        
        # Clear visualizations
        self.visualizer.clear_all()
        
        # Create database session
        self.current_session_id = self.db.create_session(self.current_user_id)
        
        # Start system-wide capture
        self.capture_manager.start_capture()
        
        # Update UI state
        self.is_session_active = True
        self.should_stop_processing = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_bar.config(text="Session active - Type anywhere!", bg='#27ae60')
        
        # Start background processing thread
        self.processing_thread = threading.Thread(target=self._process_events_loop, daemon=True)
        self.processing_thread.start()
    
    def _stop_session(self) -> None:
        """Stop the current capture session."""
        if not self.is_session_active:
            return
        
        # Stop background processing
        self.should_stop_processing = True
        
        # Stop capture
        self.capture_manager.stop_capture()
        
        # Process any remaining events
        self._process_pending_events()
        
        # Get final statistics
        cps, wpm = self.feature_extractor.get_typing_speed()
        
        # End database session
        self.db.end_session(
            self.current_session_id,
            self.feature_extractor.total_keys,
            cps,
            self.feature_extractor.error_count
        )
        
        # Save features
        summary = self.feature_extractor.get_feature_summary()
        flat_features = self._flatten_features(summary)
        self.db.save_features(self.current_session_id, flat_features)
        
        # Update UI state
        self.is_session_active = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_bar.config(text=f"Session ended - {self.keys_typed} keys captured", bg='#34495e')
        
        # Show summary
        self._show_session_summary(summary)
    
    def _process_events_loop(self) -> None:
        """Background thread to process captured events."""
        while not self.should_stop_processing:
            try:
                self._process_pending_events()
                time.sleep(0.1)  # Small delay to prevent CPU spinning
            except Exception as e:
                print(f"Error in processing loop: {e}")
    
    def _process_pending_events(self) -> None:
        """Process all pending keystroke events."""
        events = self.capture_manager.get_events()
        
        if not events:
            return
        
        # Convert to KeyEvent format for feature extractor
        key_events = [KeyEvent(e.key, e.event_type, e.timestamp) for e in events]
        
        # Save to database
        for event in events:
            self.db.save_keystroke(
                self.current_session_id,
                event.key,
                event.event_type,
                event.timestamp
            )
        
        # Extract features
        self.feature_extractor.process_events(key_events)
        
        # Update statistics
        self.keys_typed = self.feature_extractor.total_keys
        self.update_counter += len(events)
        
        # Update UI
        self._update_statistics_display()
        
        # Update visualizations periodically
        update_interval = self.config['visualization'].get('update_interval', 10)
        if self.update_counter >= update_interval:
            self._update_visualizations()
            self.update_counter = 0
        
        # Run ML prediction periodically
        prediction_interval = self.config['ml'].get('prediction_interval', 50)
        if (self.keys_typed >= prediction_interval and 
            time.time() - self.last_prediction_time > 5):  # At least 5 seconds between predictions
            self._run_ml_prediction()
            self.last_prediction_time = time.time()
    
    def _update_statistics_display(self) -> None:
        """Update statistics labels in GUI (thread-safe)."""
        def update():
            cps, wpm = self.feature_extractor.get_typing_speed()
            self.keys_label.config(text=f"Keys Typed: {self.keys_typed}")
            self.speed_label.config(text=f"Speed: {cps:.1f} CPS")
            self.wpm_label.config(text=f"WPM: {wpm:.1f}")
            self.errors_label.config(text=f"Errors: {self.feature_extractor.error_count}")
        
        self.root.after(0, update)
    
    def _update_visualizations(self) -> None:
        """Update all visualization charts (thread-safe)."""
        def update():
            try:
                # Update hold times
                if self.feature_extractor.hold_times:
                    self.visualizer.update_hold_times(
                        list(self.feature_extractor.hold_times)[-20:]
                    )
                
                # Update flight times
                if self.feature_extractor.dd_intervals or self.feature_extractor.ud_intervals:
                    self.visualizer.update_flight_times(
                        list(self.feature_extractor.dd_intervals)[-20:],
                        list(self.feature_extractor.ud_intervals)[-20:]
                    )
                
                # Update typing speed
                cps, _ = self.feature_extractor.get_typing_speed()
                if self.feature_extractor.session_end:
                    self.visualizer.update_typing_speed(
                        self.feature_extractor.session_end,
                        cps
                    )
                
                # Update error count
                self.visualizer.update_error_count(
                    self.feature_extractor.error_count,
                    self.keys_typed
                )
                
                # Refresh canvas
                self.visualizer.refresh_canvas()
            
            except Exception as e:
                print(f"Error updating visualizations: {e}")
        
        self.root.after(0, update)
    
    def _run_ml_prediction(self) -> None:
        """Run ML prediction on current typing pattern."""
        if not self.authenticator.is_trained:
            return
        
        try:
            # Get feature vector
            feature_vector = self.feature_extractor.get_feature_vector()
            
            if len(feature_vector) == 0:
                return
            
            # Predict
            is_anomaly, confidence = self.authenticator.predict_live(feature_vector)
            
            # Save prediction to database
            self.db.save_prediction(
                self.current_session_id,
                time.time(),
                is_anomaly,
                confidence
            )
            
            # Update UI
            def update_ml_status():
                if is_anomaly:
                    self.ml_status_label.config(
                        text="🔴 ANOMALY DETECTED",
                        fg='#e74c3c'
                    )
                    self.visualizer.mark_anomaly(True)
                else:
                    self.ml_status_label.config(
                        text="🟢 AUTHORIZED",
                        fg='#27ae60'
                    )
                    self.visualizer.mark_anomaly(False)
                
                self.confidence_label.config(
                    text=f"Confidence: {confidence*100:.1f}%"
                )
            
            self.root.after(0, update_ml_status)
        
        except Exception as e:
            print(f"Error in ML prediction: {e}")
    
    def _flatten_features(self, summary: dict) -> dict:
        """Flatten nested feature summary for database storage."""
        flat = {}
        for key, value in summary.items():
            if isinstance(value, dict):
                # Flatten nested dictionaries
                for subkey, subvalue in value.items():
                    # Check if subvalue is a complex type
                    if isinstance(subvalue, (list, tuple, dict)):
                        flat[f"{key}_{subkey}"] = json.dumps(subvalue)
                    else:
                        flat[f"{key}_{subkey}"] = subvalue
            elif isinstance(value, (list, tuple)):
                # Serialize lists and tuples to JSON strings
                flat[key] = json.dumps(value)
            else:
                # Keep scalar values as-is
                flat[key] = value
        return flat
    
    def _train_model(self) -> None:
        """Train ML model on historical user sessions."""
        # Get user sessions
        sessions = self.db.get_user_sessions(
            self.current_user_id,
            limit=self.config['ml'].get('min_training_sessions', 5)
        )
        
        if len(sessions) < 2:
            messagebox.showwarning(
                "Insufficient Data",
                f"Need at least 2 sessions to train model.\n"
                f"You have {len(sessions)} session(s).\n\n"
                f"Capture more typing sessions first!"
            )
            return
        
        # Extract feature vectors from sessions
        feature_vectors = []
        
        for session in sessions:
            features = self.db.get_session_features(session['session_id'])
            # Reconstruct feature vector (simplified - using available features)
            # In production, you'd reconstruct the exact same vector format
            vector = [
                features.get('hold_times_mean', 0),
                features.get('hold_times_median', 0),
                features.get('hold_times_stdev', 0),
                features.get('dd_intervals_mean', 0),
                features.get('dd_intervals_median', 0),
                features.get('dd_intervals_stdev', 0),
                features.get('ud_intervals_mean', 0),
                features.get('ud_intervals_median', 0),
                features.get('ud_intervals_stdev', 0),
                features.get('typing_speed_cps', 0),
                features.get('error_count', 0) / max(features.get('total_keys', 1), 1)
            ]
            # Pad to 21 dimensions (to match feature vector)
            vector.extend([0.1] * 10)  # Placeholder for digraph features
            
            feature_vectors.append(vector)
        
        # Train model
        try:
            stats = self.authenticator.train(feature_vectors)
            
            messagebox.showinfo(
                "Training Complete",
                f"ML model trained successfully!\n\n"
                f"Sessions used: {stats['n_sessions']}\n"
                f"Features: {stats['n_features']}\n"
                f"Contamination: {stats['contamination']*100}%\n\n"
                f"Real-time authentication is now active."
            )
            
            self.ml_status_label.config(text="⚪ MONITORING", fg='#3498db')
        
        except Exception as e:
            messagebox.showerror("Training Error", f"Failed to train model:\n{str(e)}")
    
    def _show_model_info(self) -> None:
        """Display information about the current ML model."""
        info = self.authenticator.get_model_info()
        
        if info['status'] == 'not_trained':
            messagebox.showinfo(
                "Model Info",
                "Model is not trained yet.\n\n"
                "Capture at least 5 typing sessions, then click 'Train ML Model'."
            )
        else:
            messagebox.showinfo(
                "Model Info",
                f"Model Status: {info['status'].upper()}\n\n"
                f"Feature Dimension: {info['feature_dimension']}\n"
                f"Estimators: {info['n_estimators']}\n"
                f"Contamination: {info['contamination']*100}%\n\n"
                f"Model Path: {info['model_path']}"
            )
    
    def _show_session_summary(self, summary: dict) -> None:
        """Show session summary dialog."""
        msg = f"""
Session Complete!

Total Keys: {summary['total_keys']}
Errors: {summary['error_count']}
Typing Speed: {summary['typing_speed_cps']} CPS ({summary['typing_speed_wpm']} WPM)

Hold Time:
  Mean: {summary['hold_times']['mean']:.4f}s
  Median: {summary['hold_times']['median']:.4f}s

Flight Time (DD):
  Mean: {summary['dd_intervals']['mean']:.4f}s
  
Session saved to database (ID: {self.current_session_id})
        """
        
        messagebox.showinfo("Session Summary", msg.strip())
    
    def _export_json(self) -> None:
        """Export last session to JSON."""
        if self.current_session_id is None:
            messagebox.showwarning("No Session", "No session to export")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"session_{self.current_session_id}.json"
        )
        
        if filepath:
            self.db.export_session_json(self.current_session_id, filepath)
            messagebox.showinfo("Export Complete", f"Session exported to:\n{filepath}")
    
    def _export_csv(self) -> None:
        """Export last session to CSV."""
        if self.current_session_id is None:
            messagebox.showwarning("No Session", "No session to export")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"session_{self.current_session_id}.csv"
        )
        
        if filepath:
            self.db.export_session_csv(self.current_session_id, filepath)
            messagebox.showinfo("Export Complete", f"Session exported to:\n{filepath}")
    
    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About ShadowKey Phase 2",
            "ShadowKey Phase 2\n\n"
            "System-wide keystroke capture with ML-based\n"
            "behavioral authentication.\n\n"
            "Features:\n"
            "• Global keystroke monitoring\n"
            "• Real-time feature extraction\n"
            "• ML anomaly detection (Isolation Forest)\n"
            "• Live visualization\n\n"
            "Built with Python, Tkinter, scikit-learn, and matplotlib"
        )
    
    def _on_closing(self) -> None:
        """Handle application close event."""
        if self.is_session_active:
            if messagebox.askokcancel("Session Active", "A session is active. Stop and exit?"):
                self._stop_session()
                self.db.close()
                self.root.destroy()
        else:
            self.db.close()
            self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = ShadowKeyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
