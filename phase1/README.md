# 🔑 ShadowKey - Phase 1

**Keystroke Behavior Analysis & Typing Pattern Capture**

ShadowKey is a desktop application that captures keystroke timing data and extracts typing behavior features for behavioral biometrics research and analysis.

---

## ✨ Features

### Real-time Keystroke Capture
- Records **key down** and **key up** events with microsecond precision
- Captures timestamps for every keystroke
- Works within the application's text input area

### Advanced Feature Extraction
- **Hold Times**: Duration between key press and release
- **Flight Times**: DD (down-down) and UD (up-down) intervals
- **Digraph Analysis**: Timing patterns for 2-character sequences
- **Trigraph Analysis**: Timing patterns for 3-character sequences
- **Typing Speed**: Real-time CPS (characters per second) and WPM
- **Error Tracking**: Counts backspace and delete key usage

### Data Management
- **SQLite Database**: Local, secure storage
- **Session-based Organization**: Each typing session stored separately
- **JSON Export**: Export sessions for analysis or sharing
- **Multi-user Support**: Track different users with unique IDs

### Modern UI
- Clean, professional dark-themed interface
- Real-time statistics display
- Session start/stop controls
- Export functionality

---

## 📋 Requirements

- **Python 3.7+**
- **Tkinter** (usually included with Python)
- **SQLite3** (included with Python)
- **Standard Library**: `json`, `datetime`, `statistics`

No external dependencies required! Everything uses Python's standard library.

---

## 🚀 Installation & Setup

### Step 1: Verify Python Installation

```bash
python --version
# Should show Python 3.7 or higher
```

### Step 2: Download Files

Ensure all these files are in the same directory:
```
phase1/
├── shadowkey.py          # Main application
├── keystroke_capture.py  # Capture module
├── feature_extractor.py  # Feature extraction
├── data_storage.py       # Database operations
├── config.json           # Configuration
├── README.md             # This file
└── sample_output.json    # Example output
```

### Step 3: Run the Application

```bash
cd d:\phase1
python shadowkey.py
```

---

## 📖 Usage Guide

### Starting a Capture Session

1. **Launch the application**
   ```bash
   python shadowkey.py
   ```

2. **Click "▶ Start Capture"**
   - The text area becomes active
   - Session timestamp is recorded
   - Statistics begin updating in real-time

3. **Type naturally**
   - Type any text in the input area
   - All keystrokes are captured automatically
   - Watch real-time stats update (total keys, typing speed, duration)

4. **Click "⏸ Stop & Save"**
   - Session is saved to the database
   - Features are extracted and stored
   - Summary dialog shows session statistics

5. **Export your data (optional)**
   - Click "📤 Export to JSON"
   - Choose save location
   - JSON file contains complete session data

### Understanding the Statistics

| Statistic | Description |
|-----------|-------------|
| **Status** | Current state (Idle, Recording, Saved) |
| **Session Start** | Timestamp when capture began |
| **Total Keys** | Number of keys pressed (down events) |
| **Typing Speed** | Characters per second (CPS) |
| **Duration** | Total session time in seconds |

---

## 💾 Data Storage

### Database Structure

**Location**: `shadowkey_data.db` (created automatically)

**Tables**:
1. **sessions**: Session metadata (ID, user, timestamps, key count)
2. **keystrokes**: Individual keystroke events with timestamps
3. **features**: Extracted features in JSON format

### Exported JSON Structure

```json
{
  "session_metadata": {
    "session_id": 1,
    "user_id": "default_user",
    "start_time": 1736176200.5,
    "start_time_readable": "2026-01-06T20:00:00",
    "total_keys": 112
  },
  "keystrokes": [
    {
      "key": "T",
      "timestamp": 1736176200.5,
      "event_type": "down"
    }
  ],
  "features": {
    "hold_times": { "mean_ms": 108.5, ... },
    "flight_times": { "down_down": {...}, "up_down": {...} },
    "digraphs": { "count": 111, ... },
    "trigraphs": { "count": 110, ... },
    "typing_speed": { "characters_per_second": 2.47 },
    "error_count": { "total_errors": 5 }
  }
}
```

See [sample_output.json](file:///d:/phase1/sample_output.json) for a complete example.

---

## 🔬 Feature Descriptions

### Key Hold Time
**Definition**: Time between key press (down) and release (up)

**Formula**: `hold_time = timestamp(key_up) - timestamp(key_down)`

**Use Case**: Indicates typing pressure and key depression patterns

### Flight Time - DD (Down-Down)
**Definition**: Time between consecutive key presses

**Formula**: `DD = timestamp(key_down[n+1]) - timestamp(key_down[n])`

**Use Case**: Measures typing rhythm and speed

### Flight Time - UD (Up-Down)
**Definition**: Time from key release to next key press

**Formula**: `UD = timestamp(key_down[n+1]) - timestamp(key_up[n])`

**Use Case**: Captures transition timing between keys

### Digraphs
**Definition**: Timing patterns for 2-character sequences

**Example**: "th", "he", "in"

**Use Case**: Identifies common letter pair timings unique to each typist

### Trigraphs
**Definition**: Timing patterns for 3-character sequences

**Example**: "the", "ing", "and"

**Use Case**: More complex pattern recognition for authentication

### Typing Speed
**Metrics**:
- **CPS**: Characters per second
- **WPM**: Words per minute (1 word = 5 characters)

**Use Case**: Overall typing proficiency measurement

### Error Count
**Tracks**: Backspace and Delete key presses

**Use Case**: Indicates typing accuracy and correction behavior

---

## ⚙️ Configuration

Edit [config.json](file:///d:/phase1/config.json) to customize:

```json
{
  "user_id": "your_username",
  "database_path": "shadowkey_data.db",
  "ui_settings": {
    "window_width": 900,
    "window_height": 700,
    "theme": "dark"
  }
}
```

---

## 🧪 Testing & Validation

### Quick Test

1. Run the application
2. Start a capture session
3. Type this test sentence:
   ```
   The quick brown fox jumps over the lazy dog.
   ```
4. Stop the session
5. Export to JSON and verify:
   - All keystrokes captured
   - Features calculated correctly
   - Session metadata complete

### Expected Results

For the test sentence (~45 characters):
- **Total Keys**: ~45
- **Digraphs**: ~44
- **Trigraphs**: ~43
- **Hold Times**: ~45 measurements
- **Flight Times DD**: ~44 measurements

---

## 🛠️ Troubleshooting

### Application won't start
- **Check Python version**: Must be 3.7+
- **Verify Tkinter**: Run `python -m tkinter` to test

### Database errors
- **Delete existing database**: Remove `shadowkey_data.db` and restart
- **Check file permissions**: Ensure write access to the directory

### No keystrokes captured
- **Ensure session is started**: Click "Start Capture" first
- **Type in the text area**: Must use the application's text widget
- **Check capture status**: Status should show "🔴 Recording"

### Export fails
- **Complete a session first**: Must have data to export
- **Check save location**: Ensure write permissions
- **Verify JSON format**: Open exported file in text editor

---

## 📊 Sample Usage Scenarios

### Research Study
1. Create unique `user_id` for each participant in `config.json`
2. Have participants type standardized prompts
3. Export all sessions to JSON for analysis
4. Analyze timing patterns for behavioral biometrics

### Typing Analysis
1. Capture multiple sessions over time
2. Compare typing speed improvements
3. Identify common error patterns
4. Analyze digraph/trigraph consistency

### Authentication System Development
1. Collect baseline typing patterns (enrollment)
2. Capture verification attempts
3. Compare feature vectors for authentication
4. Build machine learning models from exported data

---

## 📁 Project Structure

```
shadowkey.py              - Main application & UI (350 lines)
├─ KeystrokeCapture       - Event capture logic
├─ FeatureExtractor       - Feature calculation
├─ DataStorage            - Database operations
└─ ShadowKeyApp           - Tkinter GUI application

keystroke_capture.py      - Keystroke event handling (140 lines)
├─ KeystrokeEvent         - Event data structure
└─ KeystrokeCapture       - Capture management class

feature_extractor.py      - Feature extraction (280 lines)
└─ FeatureExtractor       - All feature calculation methods

data_storage.py           - Database operations (250 lines)
└─ DataStorage            - SQLite CRUD operations
```

---

## 🔮 Future Enhancements (Phase 2+)

- System-wide keystroke capture (using `pynput`)
- Real-time feature visualization
- Multiple text input scenarios
- Machine learning integration
- User authentication simulation
- Advanced statistics and analytics
- Web-based dashboard
- Chrome extension variant

---

## 📝 License & Acknowledgments

**ShadowKey Phase 1** - Keystroke Behavior Analysis Tool

Created for behavioral biometrics research and typing pattern analysis.

---

## 🆘 Support

For issues, questions, or feature requests:
1. Check the troubleshooting section above
2. Review [sample_output.json](file:///d:/phase1/sample_output.json) for expected data format
3. Verify all module files are present
4. Ensure Python 3.7+ is installed

---

**Ready to analyze your typing patterns? Run `python shadowkey.py` to get started! 🚀**
