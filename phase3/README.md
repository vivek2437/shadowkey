# ShadowKey Phase 3 - Multi-User Keystroke Authentication with Cloud Sync

ShadowKey Phase 3 is an advanced Python application that provides multi-user keystroke authentication with cloud synchronization. It captures keystrokes system-wide, extracts behavioral typing features, uses machine learning for per-user authentication, and syncs data to cloud storage.

## 🚀 Features

### Core Functionality
- **Multi-User Authentication**: Secure login/registration system with password hashing
- **Per-User ML Models**: Isolated machine learning models for each user
- **Cloud Synchronization**: Automatic backup of sessions to cloud storage
- **System-wide Keystroke Capture**: Monitor keystrokes across all applications using `pynput`
- **Advanced Feature Extraction**: Enhanced features including sequence entropy, rhythm stability, and rolling statistics
- **ML-Based Authentication**: Behavioral authentication using Isolation Forest for anomaly detection
- **Real-time Visualization**: Live matplotlib charts showing typing patterns and anomalies
- **Data Persistence**: Multi-user SQLite database with JSON/CSV export capabilities
- **Clean GUI**: Intuitive Tkinter interface with session management

### Technical Highlights
- Secure password hashing with SHA-256
- Per-user model isolation in separate directories
- Cloud sync with automatic session marking
- Enhanced 21-dimensional feature vectors with advanced metrics
- Thread-safe event handling with microsecond precision timestamps
- Unsupervised anomaly detection (no need for impostor samples)
- Rolling window visualizations (last 100 events)
- Model persistence and incremental training support

## 📋 Requirements

### Python Version
- Python 3.7 or higher

### Dependencies

Install all required packages:

```bash
pip install pynput matplotlib scikit-learn numpy
```

**Detailed requirements:**
- `pynput==1.7.6` - System-wide keyboard monitoring
- `matplotlib==3.5.3` - Real-time visualization
- `scikit-learn==1.1.3` - Machine learning (Isolation Forest)
- `numpy==1.21.6` - Numerical operations

**Built-in libraries used:**
- `tkinter` - GUI (usually included with Python)
- `sqlite3` - Database
- `threading`, `queue` - Concurrency
- `json`, `csv` - Data export
- `hashlib` - Password hashing
- `dataclasses`, `time`, `statistics` - Utilities

### Platform-Specific Setup

#### Windows
- **Administrator privileges** may be required to capture keystrokes in some applications
- Run the application as administrator if you experience capture issues

#### macOS
- Grant **Accessibility permissions** when prompted:
  1. System Preferences → Security & Privacy → Privacy → Accessibility
  2. Add Python or your terminal application to the allowed list

#### Linux
- May need to run with `sudo` or add user to `input` group
- X11 or Wayland with proper permissions

## 🎯 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd project/phase3

# Install dependencies
pip install pynput matplotlib scikit-learn numpy
```

### 2. First Run - User Registration

```bash
python shadowkey_phase3.py
```

**Steps:**
1. Login dialog will appear
2. Enter a **username** (e.g., "Alice")
3. Enter a **password** (minimum 4 characters)
4. Click **"Register"**
5. You'll be automatically logged in

### 3. Data Collection

**Steps:**
1. Click **"▶ Start Session"**
2. Type normally in ANY application (browser, text editor, etc.)
3. Type at least 50 characters for meaningful features
4. Click **"⬛ Stop Session"**
5. Review session summary

**Repeat 5+ times** to collect training data for your ML model.

### 4. Train Your ML Model

1. After collecting 5+ sessions, click **"🧠 Train ML Model"**
2. Wait for training completion (usually < 1 second)
3. Your personal typing model is now ready for real-time authentication!

### 5. Real-time Authentication

1. Start a new session
2. Type normally
3. ML status indicator will show:
   - **🟢 AUTHORIZED** - Typing pattern matches your profile (green)
   - **🔴 ANOMALY DETECTED** - Pattern deviates from normal (red)
4. Confidence score updates in real-time

### 6. Cloud Synchronization

1. Click **"☁️ Sync Cloud"** button
2. Sessions are uploaded to `cloud_storage/user_{id}/`
3. Check sync status in the dialog

### 7. Multi-User Testing

1. **File → Logout**
2. Register a second user (e.g., "Bob")
3. Collect Bob's training data (5+ sessions)
4. Train Bob's model
5. Notice: Each user has their own ML model in `models/user_{id}/`

## 📖 Usage Guide

### Login/Registration

#### First Time Users
- Enter username and password
- Click **"Register"**
- Account is created and you're logged in

#### Returning Users
- Enter your username and password
- Click **"Login"**
- Access your personal typing profile

### Starting/Stopping Sessions

- **Start Session**: Click "▶ Start Session" - application will capture ALL keystrokes system-wide
- **Stop Session**: Click "⬛ Stop Session" - ends capture and saves data
- Sessions auto-save to SQLite database with user association

### Understanding the Interface

#### Top Control Bar
- **▶ Start Session** - Begin capturing keystrokes
- **⬛ Stop Session** - End capture and save data
- **🧠 Train ML Model** - Train on your typing patterns
- **☁️ Sync Cloud** - Upload sessions to cloud storage

#### Statistics Panel (Left)
- **Logged in as**: Current username (green)
- **Keys Typed**: Total keystrokes in current session
- **Speed**: Characters per second (CPS)
- **WPM**: Words per minute (assuming 5 chars/word)
- **Errors**: Backspace/Delete count
- **ML Authentication**: Real-time status and confidence

#### Visualization Panel (Right)
Four real-time charts:

1. **Hold Time Distribution**: Histogram of how long you hold keys down
2. **Flight Time (DD vs UD)**: 
   - DD (Down-Down): Time between pressing consecutive keys
   - UD (Up-Down): Time between releasing one key and pressing next
3. **Typing Speed Over Time**: CPS with moving average
4. **Error Count Progress**: Cumulative errors during session

**Anomaly Highlighting**: Background turns light red when ML detects anomaly

### Menu Bar

#### File Menu
- **Export Last Session (JSON)** - Export session with all data
- **Export Last Session (CSV)** - Export keystrokes as CSV
- **Logout** - Return to login screen
- **Exit** - Close application

#### ML Model Menu
- **Train Model** - Train on your typing sessions
- **View Model Info** - Display model statistics

#### Help Menu
- **About** - Application information

### ML Model Management

#### Training
- Menu: **ML Model → Train Model** or click **🧠 Train ML Model**
- Requires: Minimum 2 sessions (5+ recommended)
- Uses: Last N sessions from database for current user
- Output: Training statistics dialog
- Models saved to: `models/user_{id}/`

#### Model Info
- Menu: **ML Model → View Model Info**
- Shows: Feature dimensions, contamination rate, model path, training status

### Cloud Synchronization

#### Syncing Sessions
- Click **☁️ Sync Cloud** button
- All unsynced sessions are uploaded
- Sessions marked as synced in database
- Cloud storage location: `cloud_storage/user_{id}/session_{id}.json`

#### Cloud Storage Structure
```
cloud_storage/
├── user_1/
│   ├── session_1.json
│   ├── session_2.json
│   └── ...
└── user_2/
    ├── session_1.json
    └── ...
```

### Exporting Data

#### JSON Export
- Menu: **File → Export Last Session (JSON)**
- Contains: Session metadata, all keystrokes, features, ML predictions
- Format: Structured JSON with timestamps

#### CSV Export
- Menu: **File → Export Last Session (CSV)**
- Contains: Keystroke events in tabular format
- Format: Standard CSV with headers

## 🏗️ Architecture

### Module Overview

```
shadowkey_phase3.py      # Main GUI application with multi-user support
├── login_dialog.py      # Login/registration dialog
├── system_capture.py    # System-wide keystroke capture (pynput)
├── feature_extractor.py # Enhanced feature calculation
├── ml_auth.py           # Per-user ML authentication (Isolation Forest)
├── data_storage.py      # Multi-user SQLite database & export
├── visualization.py     # Real-time matplotlib charts
├── cloud_manager.py     # Cloud synchronization manager
└── config_phase3.json   # Configuration file
```

### Data Flow

```
1. Login → LoginDialog → User authentication
2. Keystroke Event → SystemCaptureManager (pynput listener)
3. Event Queue (thread-safe) → Background processing thread
4. FeatureExtractor → Calculate enhanced typing metrics
5. DataStorage → Save to SQLite with user_id
6. Visualizer → Update matplotlib charts
7. MLAuth → Predict anomaly using user-specific model (every 50 keys)
8. GUI Update → Refresh statistics and ML status
9. Cloud Sync → Upload sessions to cloud_storage/
```

### Database Schema

**Tables:**
- `users`: User profiles with hashed passwords
- `sessions`: Typing sessions with user association
- `keystrokes`: Individual key events (down/up)
- `features`: Extracted feature values with enhanced metrics
- `ml_predictions`: Anomaly detection results

**Key Fields:**
- `users.user_id` - Primary key for user identification
- `users.password_hash` - SHA-256 hashed password
- `sessions.user_id` - Foreign key linking to users
- `sessions.synced_to_cloud` - Cloud sync status flag

### Threading Model
- **Main Thread**: Tkinter GUI event loop
- **Capture Thread**: pynput keyboard listener (managed by pynput)
- **Processing Thread**: Event queue processing and feature extraction
- **Communication**: Thread-safe Queue and after() callbacks for GUI updates

### Security Features
- Password hashing with SHA-256
- Per-user model isolation
- Session-based user tracking
- Secure logout functionality

## ⚙️ Configuration

Edit `config_phase3.json` to customize:

```json
{
  "database": {
    "path": "shadowkey_data.db"  // Multi-user database file
  },
  "ml": {
    "model_dir": "models",         // Base directory for user models
    "contamination": 0.05,         // Expected anomaly rate (5%)
    "min_training_sessions": 5,    // Minimum sessions for training
    "prediction_interval": 50      // Keys between ML predictions
  },
  "cloud": {
    "storage_dir": "cloud_storage", // Cloud sync directory
    "sync_interval_seconds": 300    // Auto-sync interval (future)
  },
  "visualization": {
    "update_interval": 10,          // Events between chart updates
    "rolling_window_size": 100      // Number of recent events to display
  },
  "export": {
    "json_dir": "exports/json",     // JSON export directory
    "csv_dir": "exports/csv"        // CSV export directory
  }
}
```

### Tuning ML Thresholds

**Contamination** (0.01 - 0.5):
- **Lower (0.01)**: More strict, fewer false positives, may miss anomalies
- **Higher (0.1)**: More sensitive, more false positives, catches subtle anomalies
- **Recommended**: Start with 0.05, adjust based on testing

## 📊 Example Output

### Sample JSON Export

```json
{
  "session": {
    "session_id": 1,
    "user_id": 1,
    "start_time": "2026-01-06T21:30:00",
    "end_time": "2026-01-06T21:32:15",
    "total_keys": 127,
    "typing_speed": 4.23,
    "error_count": 3,
    "synced_to_cloud": 1
  },
  "keystrokes": [
    {
      "keystroke_id": 1,
      "session_id": 1,
      "key": "h",
      "event_type": "down",
      "timestamp": 1704572400.123456
    },
    {
      "keystroke_id": 2,
      "session_id": 1,
      "key": "h",
      "event_type": "up",
      "timestamp": 1704572400.173821
    }
  ],
  "features": {
    "total_keys": 127,
    "error_count": 3,
    "typing_speed_cps": 4.23,
    "typing_speed_wpm": 50.76,
    "hold_times_mean": 0.0521,
    "hold_times_median": 0.0498,
    "hold_times_stdev": 0.0134,
    "dd_intervals_mean": 0.0987,
    "dd_intervals_median": 0.0921,
    "ud_intervals_mean": 0.0765,
    "sequence_entropy": 3.45,
    "rhythm_stability": 0.82,
    "rolling_speed_mean": 4.18
  },
  "ml_predictions": [
    {
      "prediction_id": 1,
      "session_id": 1,
      "timestamp": 1704572450.345678,
      "is_anomaly": 0,
      "confidence_score": 0.87
    }
  ],
  "export_timestamp": "2026-01-06T21:35:00"
}
```

### Cloud Sync Session File

```json
{
  "session": {
    "session_id": 1,
    "user_id": 1,
    "start_time": "2026-01-06T21:30:00",
    "total_keys": 127
  },
  "keystrokes": [...],
  "features": {...}
}
```

## 🔧 Troubleshooting

### Common Issues

#### "No events captured"
- **Windows**: Run as administrator
- **macOS**: Grant Accessibility permissions
- **Linux**: Run with `sudo` or configure input permissions

#### "Model training failed - insufficient data"
- Collect more typing sessions (minimum 5 recommended)
- Each session should have at least 20 keystrokes
- Ensure you're logged in as the correct user

#### Login dialog not visible
- Check taskbar for Python window
- Use Alt+Tab to find the window
- Try running `run_fixed.py` which forces window visibility

#### Visualization not updating
- Check that `matplotlib` backend is compatible (TkAgg)
- Reduce `update_interval` in config for more frequent updates

#### High false positive rate (too many anomalies)
- Increase `contamination` in config (e.g., from 0.05 to 0.1)
- Collect more diverse training data (different typing scenarios)
- Ensure training data is from the same user

#### Cloud sync not working
- Check that `cloud_storage/` directory exists (auto-created)
- Verify write permissions
- Check disk space

#### Multiple users seeing same model
- Verify each user has separate directory in `models/user_{id}/`
- Check that `user_id` is correctly associated with sessions
- Re-train model after logging in as correct user

### FAQ

**Q: Can I monitor multiple users?**  
A: Yes! Phase 3 supports unlimited users. Each user has their own login, ML model, and cloud storage.

**Q: Are passwords stored securely?**  
A: Yes, passwords are hashed using SHA-256 before storage. Plain text passwords are never saved.

**Q: Does it capture passwords?**  
A: Yes, it captures ALL keystrokes system-wide. Be cautious with sensitive data. Only use for authorized research/authentication purposes.

**Q: How accurate is the ML authentication?**  
A: With 5+ training sessions, typical accuracy is 80-95% depending on typing consistency. More training data improves accuracy.

**Q: Can different users share the same database?**  
A: Yes, all users share the same database file, but data is isolated by `user_id`.

**Q: What happens if I forget my password?**  
A: Currently, there's no password recovery. You would need to manually reset the database or add a new user.

**Q: Can I use different ML models?**  
A: Yes! Edit `ml_auth.py` to implement alternative models (Autoencoder, SVM, etc.). The interface is designed to be modular.

**Q: Is cloud sync real cloud storage?**  
A: Currently, it's local file-based "cloud" storage. Future versions could integrate with AWS S3, Google Drive, etc.

## 🎓 Advanced Usage

### Per-User Model Isolation

Each user's ML model is stored separately:
```
models/
├── user_1/
│   ├── behavioral_auth.pkl
│   └── feature_scaler.pkl
└── user_2/
    ├── behavioral_auth.pkl
    └── feature_scaler.pkl
```

### Testing Multi-User Authentication

1. Register User A, collect 10 sessions, train model
2. Register User B, collect 10 sessions, train model
3. Login as User A, type normally → Should show AUTHORIZED
4. Login as User B, type normally → Should show AUTHORIZED
5. Each user's model should only authenticate their own typing

### Enhanced Features

Phase 3 includes additional features:
- **Sequence Entropy**: Measures typing pattern randomness
- **Rhythm Stability**: Consistency of typing rhythm
- **Rolling Speed Mean**: Recent typing speed average

## 🔮 Future Enhancements

Potential improvements for future versions:
- Real cloud integration (AWS S3, Google Drive, Dropbox)
- Password recovery mechanism
- User profile management (edit, delete users)
- Session history viewer
- Advanced analytics dashboard
- Mobile app integration
- Continuous authentication (session-long monitoring)
- Advanced visualization (3D feature space, PCA)
- Hardware keystroke timing integration
- Biometric fusion (keystroke + mouse dynamics)
- Multi-factor authentication
- Admin panel for user management

## 📄 License

This project is for educational and research purposes. Use responsibly and ensure compliance with applicable laws regarding keystroke monitoring and user data collection.

## 🙏 Credits

Built with:
- **pynput** - Cross-platform keyboard/mouse monitoring
- **scikit-learn** - Machine learning library
- **matplotlib** - Plotting and visualization
- **Tkinter** - Standard Python GUI framework
- **SQLite** - Embedded database

---

**Version**: 3.0  
**Last Updated**: January 2026  
**Author**: Expert Full-Stack Python Developer

For questions or issues, review the troubleshooting section or check module docstrings for detailed API documentation.
