# 🚀 ShadowKey Phase 3 - Quick Start Guide

## Application is Now Running!

The **ShadowKey Phase 3** application has been successfully launched with full multi-user support.

---

## 🔐 First Time Use

### 1. Login Screen
When you start the app, you'll see the login dialog:

**To Register a New User:**
1. Enter a username (e.g., "Alice")
2. Enter a password (minimum 4 characters)
3. Click **"Register"**
4. You'll be logged in automatically

**To Login:**
1. Enter your existing username
2. Enter your password
3. Click **"Login"**

---

## 🎮 Using the Application

### Main Window Features

**Top Control Bar:**
- **▶ Start Session** - Begin capturing keystrokes
- **⬛ Stop Session** - End capture and save data
- **🧠 Train ML Model** - Train on your typing patterns (needs 5+ sessions)
- **☁️ Sync Cloud** - Upload sessions to cloud storage

**Left Panel - Statistics:**
- **Logged in as**: Shows current user
- **Keys Typed**: Real-time keystroke count
- **Speed**: Characters per second & Words per minute
- **Errors**: Backspace/Delete count
- **ML Authentication**: Shows AUTHENTICATED/ANOMALY status

**Right Panel - Visualization:**
- Real-time charts showing typing patterns
- Hold times, flight times, speed graphs

**Menu Bar:**
- **File** → Export, Logout, Exit
- **ML Model** → Train, View Info
- **Help** → About

---

## 📝 Recommended Workflow

### For New Users:

1. **Register Your Account**
   - Use the login dialog to create your account
   - Choose a memorable password

2. **Collect Training Data**
   - Click "Start Session"
   - Type naturally for 30-60 seconds
   - Click "Stop Session"
   - Repeat 5-10 times

3. **Train Your ML Model**
   - Click "Train ML Model" button
   - Wait for training to complete
   - Your unique typing pattern is now learned!

4. **Test Authentication**
   - Start a new session
   - Type naturally
   - Watch ML status - it should show "AUTHENTICATED"
   - High confidence = it recognizes you!

5. **Sync to Cloud**
   - Click "Sync Cloud" button
   - Your sessions are backed up to `cloud_storage/user_{id}/`

### Testing Multi-User Feature:

1. **Logout** (File → Logout)
2. **Register a second user** (e.g., "Bob")
3. **Record Bob's sessions** (5+ sessions)
4. **Train Bob's model**
5. **Logout Bob, Login Alice**
6. **Notice**: Each user has their own ML model!

---

## 🔬 Advanced Features Testing

### Cloud Sync:
- Sessions are automatically marked for sync
- Click "Sync Cloud" to upload
- Check `cloud_storage/user_1/session_*.json` files

### Enhanced Features:
After a session, check the database for:
- `sequence_entropy` - Typing randomness
- `rhythm_stability` - Consistency metric
- `rolling_speed_mean` - Recent typing speed

### Per-User Models:
Check the `models/` directory:
```
models/
  ├── user_1/
  │   ├── behavioral_auth.pkl
  │   └── feature_scaler.pkl
  └── user_2/
      ├── behavioral_auth.pkl
      └── feature_scaler.pkl
```

---

## 🎯 What to Look For

### During Capture:
- Real-time keystroke counter updates
- Speed (CPS/WPM) changes as you type
- Visualization charts updating
- Error count tracking backspaces

### After Training:
- ML status changes from "MONITORING" to "AUTHENTICATED" or "ANOMALY"
- Confidence percentage (70-100% = good match)
- Green = recognized, Red = anomaly detected

### Multi-User Testing:
- Different users should get different confidence scores
- User A's model should flag User B as anomaly

---

## 📂 Files Created

**During Use:**
- `shadowkey_data.db` - Multi-user database
- `models/user_{id}/` - ML models per user
- `cloud_storage/user_{id}/` - Synced sessions

**Exports:**
- Use File → Export to save sessions as JSON/CSV

---

## 🐛 Troubleshooting

**Login Dialog Not Showing:**
- Check that `login_dialog.py` exists
- Verify database permissions

**ML Training Fails:**
- Need at least 2 sessions (recommended 5+)
- Type more keystrokes per session (aim for 50+)

**Cloud Sync Issues:**
- Check `cloud_storage/` directory exists
- Verify write permissions

**Visualization Not Updating:**
- Make sure to type continuously
- Charts update every 10 keystrokes

---

## ✅ Success Indicators

You'll know Phase 3 is working when:
- ✅ Login dialog appears on startup
- ✅ Username shown in statistics panel
- ✅ Cloud sync button visible
- ✅ Models saved in `models/user_{id}/`
- ✅ ML authentication works per-user
- ✅ Sessions sync to cloud storage

---

## 🎉 Enjoy ShadowKey Phase 3!

You now have a **production-ready multi-user keystroke authentication system** with:
- Secure login/registration
- Per-user ML models
- Cloud backup
- Advanced behavioral analysis

Have fun testing your typing patterns! 🚀
