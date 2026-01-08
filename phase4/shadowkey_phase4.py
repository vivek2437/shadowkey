"""
ShadowKey Phase 4 - Multi-Modal Behavioral Biometrics Platform
Integrates Keystroke Dynamics and Voice Biometrics with Risk-Based Authentication.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import logging
from pathlib import Path
import ctypes
import numpy as np

# Ensure high DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(0)
except Exception:
    pass

# Setup paths to import from Phase 3
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
phase3_dir = project_root / 'phase3'
sys.path.append(str(phase3_dir))

# Import Phase 3 modules
try:
    from system_capture import SystemCaptureManager, KeystrokeEvent
    from feature_extractor import FeatureExtractor, KeyEvent
    from ml_auth import BehavioralAuthenticator
    from data_storage import DataStorage
    from visualization import LiveVisualizer
    from cloud_manager import CloudSyncManager
    from login_dialog import LoginDialog
except ImportError as e:
    messagebox.showerror("Setup Error", f"Failed to import Phase 3 modules: {e}\n\nPlease ensure 'phase3' directory exists and dependencies are installed.")
    sys.exit(1)

# Import Phase 4 modules
try:
    from voice_capture import VoiceCaptureManager
    from voice_features import VoiceFeatureExtractor
    from voice_auth import VoiceAuthenticator
    from fusion_engine import FusionEngine
except ImportError as e:
    # If running from same dir, standard import works, but if names clash or something...
    # Fallback/Debug
    print(f"Phase 4 import error: {e}")
    sys.exit(1)

class ShadowKeyAppPhase4:
    """
    Main application for ShadowKey Phase 4.
    Integrates Keystroke + Voice.
    """
    
    def __init__(self, root: tk.Tk, user_id: int, username: str, config_path: str = "config_phase4.json"):
        self.root = root
        self.root.title(f"ShadowKey Phase 4 (Multi-Modal) - {username}")
        self.root.geometry("1280x850")
        self.root.configure(bg='#2c3e50')
        
        self.user_id = user_id
        self.username = username
        self.config_file = config_path
        
        # Load Config
        self.config = self._load_config(config_path)
        
        # --- Initialize Core Components ---
        
        # 1. Data & Cloud (Reused)
        self.db = DataStorage(self.config['database']['path'])
        
        # 2. Keystroke (Reused)
        self.capture_manager = SystemCaptureManager()
        self.keystroke_features = FeatureExtractor()
        self.keystroke_auth = BehavioralAuthenticator(
            model_dir=self.config['ml']['model_dir'],
            user_id=user_id,
            contamination=self.config['ml']['contamination']
        )
        self.keystroke_auth.load_model()
        
        # 3. Voice (New)
        self.voice_capture = VoiceCaptureManager(sample_rate=self.config['voice']['sample_rate'])
        self.voice_features = VoiceFeatureExtractor(sample_rate=self.config['voice']['sample_rate'])
        self.voice_auth = VoiceAuthenticator(
            model_dir=self.config['ml']['model_dir'],
            user_id=user_id,
            nu=self.config['ml']['voice_nu'],
            gamma=self.config['ml']['voice_gamma']
        )
        self.voice_auth.load_model()
        
        # 4. Fusion
        self.fusion = FusionEngine(config_path)
        
        # --- State ---
        self.current_session_id = None
        self.is_session_active = False
        self.processing_thread = None
        self.should_stop_processing = False
        
        # Risk State
        self.current_keystroke_risk = None  # Start pending (needs data)
        self.current_voice_risk = 0.5     # Start neutral
        self.current_combined_risk = 0.5
        self.last_voice_check_time = 0
        
        # Stats
        self.keys_typed = 0
        self.update_counter = 0
        
        # UI
        self._create_menu()
        self._create_widgets()
        
    def _load_config(self, path: str) -> dict:
        """Load config or defaults."""
        defaults = {
            'database': {'path': 'shadowkey_phase4.db'},
            'ml': {'model_dir': 'models', 'contamination': 0.05, 'voice_nu': 0.1, 'voice_gamma': 'scale'},
            'voice': {'sample_rate': 22050, 'sample_duration': 3.0},
            'visualization': {'update_interval': 10}
        }
        try:
            with open(path, 'r') as f:
                user_conf = json.load(f)
                # Simple merge (deep merge better but keep simple)
                defaults.update(user_conf)
                return defaults
        except:
            return defaults

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self._on_closing)
        
    def _create_widgets(self):
        # Top Control Panel
        control_frame = tk.Frame(self.root, bg='#34495e', pady=10)
        control_frame.pack(fill=tk.X)
        
        # Left: Session Controls
        tk.Label(control_frame, text=" Session: ", bg='#34495e', fg='#bdc3c7').pack(side=tk.LEFT)
        
        self.start_btn = tk.Button(control_frame, text="▶ Start", command=self._start_session,
                                 bg='#27ae60', fg='white', font=('Segoe UI', 10, 'bold'), width=10)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(control_frame, text="■ Stop", command=self._stop_session,
                                bg='#e74c3c', fg='white', font=('Segoe UI', 10, 'bold'), width=10, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        # Middle: Voice Controls
        tk.Label(control_frame, text=" Voice: ", bg='#34495e', fg='#bdc3c7').pack(side=tk.LEFT)
        
        self.verify_voice_btn = tk.Button(control_frame, text="🎙️ Verify Now", command=self._verify_voice_ui,
                                        bg='#f39c12', fg='white', font=('Segoe UI', 10, 'bold'))
        self.verify_voice_btn.pack(side=tk.LEFT, padx=5)
        
        self.enroll_voice_btn = tk.Button(control_frame, text="📝 Enroll Voice", command=self._enroll_voice_ui,
                                        bg='#8e44ad', fg='white', font=('Segoe UI', 10))
        self.enroll_voice_btn.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        # Right: ML Training
        self.train_ks_btn = tk.Button(control_frame, text="🧠 Train Keystroke", command=self._train_keystroke,
                                    bg='#2980b9', fg='white')
        self.train_ks_btn.pack(side=tk.LEFT, padx=5)
        
        # Main Content
        content_frame = tk.Frame(self.root, bg='#2c3e50')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- LEFT COLUMN: RISK DASHBOARD ---
        risk_frame = tk.LabelFrame(content_frame, text="Authentication Risk Dashboard", 
                                 bg='#ecf0f1', fg='#2c3e50', font=('Segoe UI', 11, 'bold'), padx=10, pady=10, width=350)
        risk_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        # Overall Status
        self.lbl_auth_status = tk.Label(risk_frame, text="Waiting...", font=('Segoe UI', 16, 'bold'), 
                                      bg='#bdc3c7', fg='#2c3e50', width=20, pady=10)
        self.lbl_auth_status.pack(fill=tk.X, pady=10)
        
        # Risk Meter
        tk.Label(risk_frame, text="Combined Risk Score:", bg='#ecf0f1').pack(anchor='w')
        self.risk_bar = ttk.Progressbar(risk_frame, length=300, mode='determinate')
        self.risk_bar.pack(fill=tk.X, pady=5)
        self.lbl_risk_val = tk.Label(risk_frame, text="0.00", bg='#ecf0f1', font=('Consolas', 10))
        self.lbl_risk_val.pack(anchor='e')
        
        ttk.Separator(risk_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Individual Factors
        tk.Label(risk_frame, text="Risk Factors:", bg='#ecf0f1', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        
        # Keystroke
        f_ks = tk.Frame(risk_frame, bg='#ecf0f1')
        f_ks.pack(fill=tk.X, pady=5)
        tk.Label(f_ks, text="Keystroke:", bg='#ecf0f1', width=10, anchor='w').pack(side=tk.LEFT)
        self.lbl_ks_risk = tk.Label(f_ks, text="Unknown", bg='#95a5a6', fg='white', width=10)
        self.lbl_ks_risk.pack(side=tk.LEFT, padx=5)
        
        # Voice
        f_mc = tk.Frame(risk_frame, bg='#ecf0f1')
        f_mc.pack(fill=tk.X, pady=5)
        tk.Label(f_mc, text="Voice:", bg='#ecf0f1', width=10, anchor='w').pack(side=tk.LEFT)
        self.lbl_vc_risk = tk.Label(f_mc, text="Not Verified", bg='#95a5a6', fg='white', width=10)
        self.lbl_vc_risk.pack(side=tk.LEFT, padx=5)
        
        # --- RIGHT COLUMN: VISUALIZATION & LOGS ---
        right_frame = tk.Frame(content_frame, bg='#2c3e50')
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Feature Viz (Reused from Phase 3 but just hold times for now)
        viz_frame = tk.LabelFrame(right_frame, text="Live Keystroke Metrics", bg='#ecf0f1')
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.visualizer = LiveVisualizer(viz_frame, rolling_window=50)
        
        # Activity Log
        log_frame = tk.LabelFrame(right_frame, text="System Log", bg='#ecf0f1')
        log_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        self.log_text = tk.Text(log_frame, height=8, bg='black', fg='#00ff00', font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Status Bar
        self.status_bar = tk.Label(self.root, text="Ready", bg='#34495e', fg='white', anchor='w', padx=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Check models
        self.log(f"Keystroke Model: {'LOADED' if self.keystroke_auth.is_trained else 'NOT TRAINED'}")
        self.log(f"Voice Model: {'LOADED' if self.voice_auth.is_trained else 'NOT TRAINED'}")

    def log(self, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)

    def _start_session(self):
        if self.is_session_active: return
        
        # Reset
        self.keystroke_features.reset()
        self.keys_typed = 0
        self.update_counter = 0
        self.visualizer.clear_all()
        
        # DB Session
        self.current_session_id = self.db.create_session(self.user_id)
        
        # Start Capture
        self.capture_manager.start_capture()
        self.is_session_active = True
        
        # UI
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.lbl_auth_status.config(text="MONITORING", bg='#f1c40f')
        self.log("Session started.")
        
        # Thread
        self.should_stop_processing = False
        self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processing_thread.start()

    def _stop_session(self):
        if not self.is_session_active: return
        
        self.should_stop_processing = True
        self.capture_manager.stop_capture()
        
        # Save session stats
        cps, _ = self.keystroke_features.get_typing_speed()
        self.db.end_session(self.current_session_id, self.keystroke_features.total_keystrokes, cps, self.keystroke_features.error_count)
        
        # Save features for training
        features = self.keystroke_features.get_feature_summary()
        self.db.save_features(self.current_session_id, features)
        
        # UI
        self.is_session_active = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.lbl_auth_status.config(text="STOPPED", bg='#bdc3c7')
        self.log("Session stopped.")

    def _process_loop(self):
        """Main processing loop for keystrokes + risk updates."""
        while not self.should_stop_processing:
            try:
                # 1. Process Keystrokes
                events = self.capture_manager.get_events()
                if events:
                    key_events = [KeyEvent(e.key, e.event_type, e.timestamp) for e in events]
                    self.keystroke_features.process_events(key_events)
                    self.keys_typed += len(events)
                    
                    # Update Visualizer (Throttle)
                    if self.keys_typed % 10 == 0:
                        self._update_viz()
                    
                    # Periodic ML Prediction (every 12 keys now)
                    if self.keys_typed % 12 == 0 and self.keystroke_auth.is_trained:
                        self._check_keystroke_risk()

                time.sleep(0.05)
            except Exception as e:
                print(f"Loop error: {e}")

    def _update_viz(self):
        """Update chart in main thread."""
        def _u():
            # 1. Hold Times
            if self.keystroke_features.hold_times:
                self.visualizer.update_hold_times(list(self.keystroke_features.hold_times)[-20:])
            
            # 2. Flight Times
            if self.keystroke_features.flight_times_dd:
                self.visualizer.update_flight_times(
                    list(self.keystroke_features.flight_times_dd)[-20:],
                    list(self.keystroke_features.flight_times_ud)[-20:]
                )
                
            # 3. Typing Speed
            cps, _ = self.keystroke_features.get_typing_speed()
            self.visualizer.update_typing_speed(time.time(), cps)
            
            # 4. Error Count
            self.visualizer.update_error_count(self.keystroke_features.error_count, self.keystroke_features.total_keystrokes)
            
            self.visualizer.refresh_canvas()
        
        self.root.after(0, _u)

    def _check_keystroke_risk(self):
        """Run Keystroke ML and update risk."""
        vec = self.keystroke_features.get_feature_vector()
        if not vec: return
        
        is_anomaly, conf = self.keystroke_auth.predict_live(vec)
        
        # Calculate Risk (Risk = 1.0 if Anomaly, else 1-Conf)
        if is_anomaly:
            risk = 0.8 + (1-conf)*0.2 # High risk base
        else:
            risk = 1.0 - conf # Low risk
            
        self.current_keystroke_risk = risk
        self._update_fusion_display()

    def _verify_voice_ui(self):
        """Trigger voice verification."""
        if not self.voice_auth.is_trained:
            messagebox.showwarning("Voice Model", "Voice model not trained. Please Enroll Voice first.")
            return

        # Show mini dialog
        top = tk.Toplevel(self.root)
        top.title("Voice Verification")
        top.geometry("300x150")
        
        lbl = tk.Label(top, text="Click Record and say the passphrase:\n\n'My voice is my password'", font=('Segoe UI', 10))
        lbl.pack(pady=10)
        
        btn = tk.Button(top, text="🔴 Record (3s)", bg='#e74c3c', fg='white',
                      command=lambda: self._run_voice_verify_thread(top, btn))
        btn.pack(pady=10)

    def _run_voice_verify_thread(self, dialog, btn):
        btn.config(state=tk.DISABLED, text="Recording...")
        self.root.update()
        
        def task():
            # Record
            audio = self.voice_capture.record_sample(duration=self.config['voice']['sample_duration'])
            if audio is None:
                self.root.after(0, lambda: messagebox.showerror("Error", "Recording failed"))
                self.root.after(0, dialog.destroy)
                return

            # Extract
            feats = self.voice_features.extract_features(audio)
            if feats is None:
                self.root.after(0, lambda: messagebox.showerror("Error", "Could not extract features (too quiet?)"))
                self.root.after(0, dialog.destroy)
                return

            # Predict
            is_valid, conf = self.voice_auth.predict(feats)
            
            # Update Risk
            if is_valid:
                self.current_voice_risk = 1.0 - conf
                msg = f"Voice Verified! (Conf: {conf:.2f})"
                color = '#27ae60'
            else:
                self.current_voice_risk = 0.9
                msg = f"Voice Rejected! (Conf: {conf:.2f})"
                color = '#c0392b'
                
            self.root.after(0, lambda: self.log(msg))
            self.root.after(0, lambda: self._update_fusion_display())
            self.root.after(0, dialog.destroy)
        
        threading.Thread(target=task, daemon=True).start()

    def _update_fusion_display(self):
        """Re-calculate weighted risk and update GUI."""
        # Calculate
        ks_risk = self.current_keystroke_risk if self.current_keystroke_risk is not None else 0.5
        
        final_risk = self.fusion.calculate_risk(
            keystroke_confidence=1.0 - ks_risk,
            voice_confidence=1.0 - self.current_voice_risk 
        )
        
        level_const = self.fusion.decide_auth_level(final_risk)
        
        # Map Level to UI
        if level_const == FusionEngine.RISK_LOW:
            status_text = "TRUSTED"
            status_bg = '#27ae60' # Green
        elif level_const == FusionEngine.RISK_MEDIUM:
            status_text = "VERIFY"
            status_bg = '#f39c12' # Orange
        else:
            status_text = "HIGH RISK"
            status_bg = '#c0392b' # Red
            
        def _ui():
            # Update Overall
            self.lbl_auth_status.config(text=status_text, bg=status_bg)
            self.risk_bar['value'] = final_risk * 100
            self.lbl_risk_val.config(text=f"{final_risk:.2f}")
            
            # Update Factors
            if self.current_keystroke_risk is None:
                self.lbl_ks_risk.config(text="Pending...", bg='#95a5a6')
            else:
                self.lbl_ks_risk.config(text=f"{self.current_keystroke_risk:.2f}", bg='#34495e')
            
            
            if self.current_voice_risk > 0.8:
                self.lbl_vc_risk.config(text="HIGH", bg='#e74c3c')
            elif self.current_voice_risk < 0.4:
                self.lbl_vc_risk.config(text="LOW", bg='#27ae60')
            else:
                self.lbl_vc_risk.config(text="MED", bg='#f1c40f')
                
        self.root.after(0, _ui)

    def _enroll_voice_ui(self):
        """Voice Enrollment Dialog."""
        samples_needed = self.config['voice'].get('min_samples_for_training', 3)
        self.enroll_samples = []
        
        top = tk.Toplevel(self.root)
        top.title("Enroll Voice")
        top.geometry("350x250")
        
        lbl_instr = tk.Label(top, text=f"We need {samples_needed} voice samples.\nClick Record and say the passphrase.", pady=10)
        lbl_instr.pack()
        
        lbl_progress = tk.Label(top, text=f"Samples collected: 0 / {samples_needed}", font=('bold'))
        lbl_progress.pack(pady=5)
        
        def record_step():
            btn_rec.config(state=tk.DISABLED, text="Recording...")
            self.root.update()
            
            # Blocking record
            audio = self.voice_capture.record_sample(duration=self.config['voice']['sample_duration'])
            
            if audio is not None:
                feats = self.voice_features.extract_features(audio)
                if feats is not None:
                    self.enroll_samples.append(feats)
                    lbl_progress.config(text=f"Samples collected: {len(self.enroll_samples)} / {samples_needed}")
                else:
                    messagebox.showerror("Error", "Audio unusable (silence?). Try again.")
            
            btn_rec.config(state=tk.NORMAL, text="🔴 Record Sample")
            
            if len(self.enroll_samples) >= samples_needed:
                btn_rec.config(state=tk.DISABLED)
                btn_train.config(state=tk.NORMAL)
                messagebox.showinfo("Done", "Samples collected. Click Train.")

        btn_rec = tk.Button(top, text="🔴 Record Sample", command=record_step, bg='#e74c3c', fg='white', padx=10, pady=5)
        btn_rec.pack(pady=10)
        
        def finish_training():
            res = self.voice_auth.train(self.enroll_samples)
            if res.get('status') == 'success':
                self.log("Voice Model-Trained Successfully.")
                messagebox.showinfo("Success", "Voice model trained!")
                top.destroy()
            else:
                messagebox.showerror("Error", "Training failed.")
                
        btn_train = tk.Button(top, text="Train Model", command=finish_training, state=tk.DISABLED, bg='#2980b9', fg='white')
        btn_train.pack(pady=10)

    def _train_keystroke(self):
        """Trigger existing Phase 3 keystroke training."""
        sessions = self.db.get_user_sessions(self.user_id, limit=20) # Increase limit
        if len(sessions) < 2:
            messagebox.showwarning("Data", "Need at least 2 sessions to train.")
            return
            
        vecs = []
        for s in sessions:
            f = self.db.get_session_features(s['session_id'])
            if not f: continue
            
            # Reconstruct vector matching Phase 3 FeatureExtractor.get_feature_vector (26 dims)
            vec = []
            
            # 1. Basic Stats (2)
            vec.append(f.get('total_keystrokes', 0))
            vec.append(f.get('error_count', 0))
            
            # 2. Speed (2)
            vec.append(f.get('typing_speed_cps', 0))
            vec.append(f.get('typing_speed_wpm', 0))
            
            # 3. Hold Times (4)
            vec.append(f.get('hold_times_mean', 0)) # mean
            vec.append(f.get('hold_times_stdev', 0)) # std
            vec.append(f.get('hold_times_min', 0)) # min (assuming saved or 0)
            vec.append(f.get('hold_times_max', 0)) # max
            
            # 4. Flight DD (2)
            vec.append(f.get('dd_intervals_mean', 0)) # mean
            vec.append(f.get('dd_intervals_stdev', 0)) # std
            
            # 5. Flight UD (2)
            vec.append(f.get('ud_intervals_mean', 0)) # mean
            vec.append(f.get('ud_intervals_stdev', 0)) # std
            
            # 6. Top Digraphs (10) - Assuming DB doesn't store them individually easily, 
            # we fill with 0 or stored 'common_digraphs_avg' if available.
            # Simplified: Fill 10 slots with average DD (better than 0) or 0
            # Phase 3 extractor puts actual values here.
            # For retro-compatibility, we pad with 0.
            vec.extend([0]*10)
            
            # 7. Enhanced Features (4)
            vec.append(f.get('sequence_entropy', 0))
            vec.append(f.get('rhythm_stability', 0))
            vec.append(f.get('rolling_speed_mean', 0))
            vec.append(f.get('rolling_speed_std', 0))
            
            vecs.append(vec)
            
        if not vecs:
            messagebox.showwarning("Data", "No valid session data found.")
            return

        self.keystroke_auth.train(vecs)
        self.log("Keystroke Model Trained.")
        
        # Immediate update using last session
        if vecs:
            last_vec = vecs[-1]
            is_anomaly, conf = self.keystroke_auth.predict_live(last_vec)
            if is_anomaly:
                self.current_keystroke_risk = 0.8 + (1-conf)*0.2
            else:
                self.current_keystroke_risk = 1.0 - conf
            self._update_fusion_display()
            
        messagebox.showinfo("Success", "Keystroke model trained. Dashboard updated.")

    def _on_closing(self):
        if self.is_session_active:
            self._stop_session()
        self.db.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    # root.withdraw() # Caused transient dialogs to hide
    root.attributes('-alpha', 0.0) # Hide visually but keep active
    
    # Login (Reuse Phase 3 Login)
    # We need a dummy DB object for login dialog
    temp_db = DataStorage("shadowkey_phase4.db") 
    login = LoginDialog(root, temp_db)
    
    # Ensure dialog is visible even if parent is transparent
    # Force focus/lift
    login.dialog.attributes('-topmost', True)
    login.dialog.after(100, lambda: login.dialog.attributes('-topmost', False))
    
    user_id, username = login.show()
    temp_db.close()
    
    if user_id:
        root.attributes('-alpha', 1.0) # Restore visibility
        root.deiconify()
        app = ShadowKeyAppPhase4(root, user_id, username)
        root.mainloop()
    else:
        root.destroy()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open("crash_log.txt", "w") as f:
            f.write(traceback.format_exc())
        messagebox.showerror("Crash", f"App crashed!\nSee crash_log.txt\n{e}")
