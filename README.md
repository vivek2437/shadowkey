# ShadowKey

**Zero-Trust Behavioral Authentication Platform**

ShadowKey is an enterprise-grade, AI-powered continuous authentication system that uses behavioral biometrics (keystroke dynamics, voice recognition, and behavioral patterns) to provide real-time identity verification without interrupting user workflows.

## ✨ Features

- **🔐 Zero-Trust Architecture**: Continuous identity verification with no implicit trust
- **⌨️ Keystroke Dynamics**: Real-time typing pattern analysis
- **🎤 Voice Biometrics**: Multi-factor authentication via voice recognition
- **📊 Behavioral Analysis**: Device fingerprinting and usage pattern monitoring
- **📈 Dynamic Trust Scoring**: Real-time risk assessment (0-100 scale)
- **🚨 Adaptive Authentication**: Auto-step-up challenges for anomalous behavior
- **🎯 WebSocket Integration**: Live biometric data streaming

## 🏗️ Architecture

```
shadowkey/
├── secure-flow-main/        # React + TypeScript Frontend
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── hooks/           # Keystroke capture hook
│   │   ├── pages/           # Dashboard, Auth pages
│   │   └── services/        # API & WebSocket clients
│   └── vercel.json          # Frontend deployment config
│
└── phase5/api/              # FastAPI Backend
    ├── auth_service.py      # Main API routes
    ├── requirements.txt     # Python dependencies
    └── vercel.json          # Backend deployment config
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **Git**

### Local Development

#### 1. Clone the Repository

```bash
git clone https://github.com/vivek2437/shadowkey.git
cd shadowkey
```

#### 2. Start the Backend

```bash
cd phase5/api
pip install -r requirements.txt
python auth_service.py
```

Backend runs on `http://localhost:8000`

#### 3. Start the Frontend

```bash
cd secure-flow-main/secure-flow-main
npm install
npm run dev
```

Frontend runs on `http://localhost:8080`

#### 4. Access the App

1. Navigate to `http://localhost:8080/auth/sign-in`
2. Login with any credentials (e.g., `john.doe@acme.com` / `password123`)
3. Type in the Testing Playground to see keystroke scores update
4. Complete voice enrollment for full biometric coverage

## 🌐 Deployment to Vercel

### Frontend Deployment

```bash
cd secure-flow-main/secure-flow-main
vercel --prod
```

Set environment variable in Vercel dashboard:
- `VITE_API_BASE_URL` = `https://your-backend.vercel.app`

### Backend Deployment

```bash
cd phase5/api
vercel --prod
```

Update frontend `.env` with your deployed backend URL.

**📖 Detailed Instructions:** See [DEPLOYMENT.md](./DEPLOYMENT.md)

## 🔧 Environment Variables

### Frontend (`.env`)

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Backend

No environment variables required for basic deployment.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | User authentication |
| `POST` | `/auth/keystroke` | Submit keystroke data |
| `POST` | `/auth/voice/enroll` | Enroll voice baseline |
| `POST` | `/auth/voice/verify` | Verify voice sample |
| `GET` | `/auth/risk` | Get current trust score |
| `WS` | `/auth/continuous` | Real-time biometric stream |

## 🎨 Tech Stack

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + shadcn/ui
- **3D Graphics**: Three.js + React Three Fiber
- **State Management**: React Hooks
- **HTTP Client**: Axios
- **Real-time**: WebSockets

### Backend
- **Framework**: FastAPI
- **Runtime**: Python 3.11
- **WebSockets**: FastAPI native WS
- **Data Models**: Pydantic

## 📊 How It Works

1. **Login**: User authenticates with credentials
2. **Baseline Capture**: System collects initial keystroke & voice samples
3. **Continuous Monitoring**: WebSocket streams typing patterns in real-time
4. **Risk Calculation**: Multi-modal fusion algorithm computes trust score
   - Keystroke: 40% weight
   - Voice: 40% weight  
   - Behavioral: 20% weight
5. **Adaptive Response**:
   - **Low Risk** (70+): Normal access
   - **Medium Risk** (50-70): Step-up challenge
   - **High Risk** (<50): Session termination

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push and create a Pull Request

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details

## 👤 Author

**ShadowKey Team**
- GitHub: [@vivek2437](https://github.com/vivek2437)

## 🙏 Acknowledgments

- Built for enterprise Zero-Trust security requirements
- Inspired by NIST SP 800-63B biometric authentication standards

---

**⚠️ Security Note**: This is a demonstration platform. For production use, implement proper encryption, secure storage, and compliance with data protection regulations (GDPR, CCPA, etc.).
