import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Shield,
  LogOut,
  User,
  Settings,
  Activity,
  Fingerprint,
  Mic,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Bell,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useKeystrokeDynamics } from '@/hooks/useKeystrokeDynamics';
import { socketService } from '@/services/socket';
import { authApi } from '@/services/api';
import VoiceVerifier from '@/components/VoiceVerifier';
import VoiceEnrollmentModal from '@/components/VoiceEnrollmentModal';
import { ThreeHeroBackground } from '@/components/ui/three-hero-background';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

// Mock data
const mockUser = {
  name: 'John Doe',
  email: 'john.doe@acme.com',
  company: 'Acme Inc.',
  avatar: null,
};

// Initial state - Zero Trust: Start with null or low scores
const initialTrustData = {
  overall: 0,
  keystroke: null as number | null,
  voice: null as number | null,
  behavioral: null as number | null,
};

const initialSession = {
  status: 'active',
  startTime: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  lastVerification: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
  riskLevel: 'initializing' as 'low' | 'medium' | 'high' | 'initializing',
};

const initialActivity: Array<{ time: string; action: string; status: string }> = [
  // Activity log will be populated with real events from WebSocket and API calls
];

// Components
const TrustScoreCard: React.FC<{ score: number | null; label: string; icon: React.ReactNode }> = ({
  score,
  label,
  icon,
}) => {
  const isAwaiting = score === null;
  const displayText = isAwaiting
    ? (label.includes('Keystroke') ? 'Awaiting input' : label.includes('Voice') ? 'Not verified' : 'N/A')
    : `${score.toFixed(1)}%`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card-enterprise p-6"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-accent flex items-center justify-center">
          {icon}
        </div>
        <span className="text-muted-foreground font-medium">{label}</span>
      </div>
      <div className="flex items-end justify-between">
        <span className={cn(
          "font-bold",
          isAwaiting ? "text-muted-foreground text-sm" : "text-3xl text-foreground"
        )}>
          {displayText}
        </span>
        {!isAwaiting && (
          <div className="h-2 flex-1 ml-4 bg-secondary rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${score}%` }}
              transition={{ duration: 1, delay: 0.2 }}
              className={cn(
                'h-full rounded-full',
                score >= 90 ? 'bg-success' : score >= 70 ? 'bg-warning' : 'bg-destructive'
              )}
            />
          </div>
        )}
      </div>
    </motion.div>
  );
};

const RiskBadge: React.FC<{ level: 'low' | 'medium' | 'high' | 'initializing' }> = ({ level }) => {
  const config = {
    low: { label: 'Low Risk', className: 'risk-badge-low' },
    medium: { label: 'Medium Risk', className: 'risk-badge-medium' },
    high: { label: 'High Risk', className: 'risk-badge-high' },
    initializing: { label: 'Initializing', className: 'bg-muted text-muted-foreground border-muted-foreground/20' },
  };

  const currentConfig = config[level] || config.initializing;

  return (
    <span className={cn('px-3 py-1 rounded-full text-sm font-medium border', currentConfig.className)}>
      {currentConfig.label}
    </span>
  );
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  // useKeystrokeDynamics moved to App.tsx for global capture

  const [trustData, setTrustData] = React.useState(initialTrustData);
  const [sessionStatus, setSessionStatus] = React.useState(initialSession);
  const [voiceCheckRequired, setVoiceCheckRequired] = React.useState(false);
  const [activityLog, setActivityLog] = React.useState(initialActivity);

  const addActivity = (action: string, status: 'success' | 'warning' | 'info' = 'success') => {
    setActivityLog(prev => [
      { time: 'Just now', action, status },
      ...prev.slice(0, 4) // Keep last 5 items
    ]);
  };

  // Enrollment tracking
  const [isVoiceEnrolled, setIsVoiceEnrolled] = React.useState(false);
  const [isKeystrokeEnrolled, setIsKeystrokeEnrolled] = React.useState(false);
  const [showEnrollmentModal, setShowEnrollmentModal] = React.useState(false);
  const isInitializing = !isVoiceEnrolled && !isKeystrokeEnrolled;

  // Auto-trigger voice enrollment modal
  React.useEffect(() => {
    if (!isVoiceEnrolled) {
      const timer = setTimeout(() => {
        setShowEnrollmentModal(true);
      }, 2000); // 2 seconds after mount
      return () => clearTimeout(timer);
    }
  }, [isVoiceEnrolled]);

  React.useEffect(() => {
    socketService.connect();

    // Initial fetch of risk status
    const fetchRiskScore = () => {
      authApi.getRiskScore()
        .then(data => {
          setTrustData(prev => ({
            ...prev,
            overall: data.trust_score,
            keystroke: data.keystroke_score !== undefined ? data.keystroke_score : prev.keystroke,
            voice: data.voice_score !== undefined ? data.voice_score : prev.voice,
            behavioral: data.behavioral_score !== undefined ? data.behavioral_score : prev.behavioral
          }));
          setSessionStatus(prev => ({ ...prev, riskLevel: (data.risk_level?.toLowerCase() || 'initializing') as any }));

          // Sync enrollment states
          if (data.keystroke_score !== null && data.keystroke_score !== undefined) setIsKeystrokeEnrolled(true);
          if (data.voice_score !== null && data.voice_score !== undefined) setIsVoiceEnrolled(true);
        })
        .catch(err => console.error("Failed to fetch risk score:", err));
    };

    fetchRiskScore();

    // Polling interval ref
    const pollingRef = { current: null as NodeJS.Timeout | null };

    const startPolling = () => {
      if (!pollingRef.current) {
        console.log('Starting risk polling...');
        pollingRef.current = setInterval(fetchRiskScore, 5000);
      }
    };

    const stopPolling = () => {
      if (pollingRef.current) {
        console.log('Stopping risk polling...');
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };

    // Subscribe to WS messages
    const unsubscribeMessages = socketService.subscribe((message: any) => {
      console.log('WS Message Received:', message);

      if (message.type === 'enrollment_complete') {
        const payload = message.payload;
        if (payload.biometric === 'voice') {
          setIsVoiceEnrolled(true);
          setTrustData(prev => ({
            ...prev,
            voice: payload.voice_score,
            overall: payload.trust_score,
            behavioral: payload.behavioral_score ?? prev.behavioral
          }));
          addActivity(`Voice baseline captured`, 'success');
        } else if (payload.biometric === 'keystroke') {
          setIsKeystrokeEnrolled(true);
          setTrustData(prev => ({
            ...prev,
            keystroke: payload.keystroke_score,
            overall: payload.trust_score,
            behavioral: payload.behavioral_score ?? prev.behavioral
          }));
          addActivity(`Keystroke baseline captured`, 'success');
        }
      }

      if (message.type === 'trust_update') {
        const payload = message.payload;
        setTrustData(prev => ({
          ...prev,
          overall: payload.trust_score ?? prev.overall,
          keystroke: payload.keystroke_score ?? prev.keystroke,
          voice: payload.voice_score ?? prev.voice,
          behavioral: payload.behavioral_score ?? prev.behavioral,
        }));
        if (payload.keystroke_score) addActivity(`Keystroke verification successful`, 'success');
        if (payload.voice_score) addActivity(`Voice verification successful`, 'success');
      }

      if (message.type === 'decision') {
        if (message.payload.decision === 'STEP_UP') {
          setVoiceCheckRequired(true);
          toast.warning("Identity verification required.");
        }
        if (message.payload.decision === 'TERMINATE') {
          toast.error("Session terminated due to high risk.");
          socketService.disconnect();
          navigate('/auth/signin');
        }
        if (message.payload.decision === 'VERIFIED') {
          setTrustData(prev => ({
            ...prev,
            voice: message.payload.voice_score ?? prev.voice,
            overall: message.payload.trust_score ?? prev.overall,
          }));
          addActivity(`Voice verification passed`, 'success');
        }
      }

      if (message.type === 'risk_update') {
        setSessionStatus(prev => ({
          ...prev,
          riskLevel: message.payload.risk_level?.toLowerCase() || 'low'
        }));
      }
    });

    // Subscribe to connection state
    const unsubscribeConnection = socketService.onConnectionChange((isConnected) => {
      if (isConnected) {
        stopPolling();
      } else {
        startPolling();
      }
    });

    return () => {
      unsubscribeMessages();
      unsubscribeConnection();
      stopPolling();
      socketService.disconnect();
    };
  }, [navigate]);

  const handleVoiceComplete = (success: boolean) => {
    if (success) {
      setVoiceCheckRequired(false);
      // Optional: Notify backend we are done, though backend verify endpoint handles it
    }
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen bg-secondary/30 relative overflow-hidden">
      <ThreeHeroBackground trustScore={trustData.overall / 100} />
      {/* Header */}
      <header className="bg-background border-b border-border sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
              <Shield className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-foreground">ShadowKey</span>
          </Link>

          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-primary rounded-full" />
            </Button>
            <Button variant="ghost" size="icon">
              <Settings className="w-5 h-5" />
            </Button>
            <Button asChild variant="ghost" size="sm">
              <Link to="/">
                <LogOut className="w-4 h-4 mr-2" />
                Sign Out
              </Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Welcome Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Welcome back, {mockUser.name.split(' ')[0]}
          </h1>
          <p className="text-muted-foreground">
            Your session is secure. All biometrics are actively monitoring.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - Trust Scores */}
          <div className="lg:col-span-2 space-y-6">
            {/* Overall Trust Score */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="card-enterprise p-8"
            >
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-foreground mb-1">Overall Trust Score</h2>
                  <p className="text-muted-foreground">Based on continuous behavioral analysis</p>
                </div>
                <RiskBadge level={sessionStatus.riskLevel} />
              </div>

              <div className="flex items-center gap-8">
                <div className="relative w-32 h-32">
                  {isInitializing ? (
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="text-center">
                        <span className="text-2xl text-muted-foreground">--</span>
                        <p className="text-xs text-muted-foreground mt-2">Initializing</p>
                      </div>
                    </div>
                  ) : (
                    <>
                      <svg className="w-full h-full transform -rotate-90">
                        <circle
                          cx="64"
                          cy="64"
                          r="56"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="none"
                          className="text-secondary"
                        />
                        <motion.circle
                          cx="64"
                          cy="64"
                          r="56"
                          stroke="url(#trustGradient)"
                          strokeWidth="8"
                          fill="none"
                          strokeLinecap="round"
                          initial={{ strokeDasharray: '0 352' }}
                          animate={{ strokeDasharray: `${trustData.overall * 3.52} 352` }}
                          transition={{ duration: 1.5, ease: 'easeOut' }}
                        />
                        <defs>
                          <linearGradient id="trustGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="hsl(142, 71%, 45%)" />
                            <stop offset="100%" stopColor="hsl(226, 70%, 55%)" />
                          </linearGradient>
                        </defs>
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-4xl font-bold text-foreground">{trustData.overall?.toFixed(1)}</span>
                      </div>
                    </>
                  )}
                </div>

                <div className="flex-1 grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-secondary rounded-xl">
                    <Fingerprint className="w-6 h-6 text-primary mx-auto mb-2" />
                    <p className="text-2xl font-bold text-foreground">
                      {trustData.keystroke !== null ? `${trustData.keystroke.toFixed(1)}%` : '--'}
                    </p>
                    <p className="text-xs text-muted-foreground">Keystroke</p>
                  </div>
                  <div className="text-center p-4 bg-secondary rounded-xl">
                    <Mic className="w-6 h-6 text-primary mx-auto mb-2" />
                    <p className="text-2xl font-bold text-foreground">
                      {trustData.voice !== null ? `${trustData.voice.toFixed(1)}%` : '--'}
                    </p>
                    <p className="text-xs text-muted-foreground">Voice</p>
                  </div>
                  <div className="text-center p-4 bg-secondary rounded-xl">
                    <Activity className="w-6 h-6 text-primary mx-auto mb-2" />
                    <p className="text-2xl font-bold text-foreground">
                      {trustData.behavioral !== null ? `${trustData.behavioral.toFixed(1)}%` : '--'}
                    </p>
                    <p className="text-xs text-muted-foreground">Behavioral</p>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Trust Score Breakdown */}
            <div className="grid md:grid-cols-3 gap-4">
              <TrustScoreCard
                score={trustData.keystroke}
                label="Keystroke Dynamics"
                icon={<Fingerprint className="w-5 h-5 text-primary" />}
              />
              <div className="relative group">
                <TrustScoreCard
                  score={trustData.voice}
                  label="Voice Biometrics"
                  icon={<Mic className="w-5 h-5 text-primary" />}
                />
                <Button
                  variant="outline"
                  size="sm"
                  className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => setVoiceCheckRequired(true)}
                >
                  Verify Now
                </Button>
              </div>
              <TrustScoreCard
                score={trustData.behavioral}
                label="Behavioral Analysis"
                icon={<TrendingUp className="w-5 h-5 text-primary" />}
              />
            </div>
          </div>

          {/* Right Column - Session & Activity */}
          <div className="space-y-6">
            {/* Session Status */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="card-enterprise p-6"
            >
              <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-primary" />
                Session Status
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Status</span>
                  <span className="flex items-center gap-2 text-success font-medium">
                    <span className="w-2 h-2 bg-success rounded-full animate-pulse" />
                    Active
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Started</span>
                  <span className="text-foreground">{formatTime(sessionStatus.startTime)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Last Verified</span>
                  <span className="text-foreground">{formatTime(sessionStatus.lastVerification)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Risk Level</span>
                  <RiskBadge level={sessionStatus.riskLevel} />
                </div>
              </div>
            </motion.div>

            {/* User Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="card-enterprise p-6"
            >
              <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                <User className="w-5 h-5 text-primary" />
                Profile
              </h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-accent flex items-center justify-center">
                    <User className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">{mockUser.name}</p>
                    <p className="text-sm text-muted-foreground">{mockUser.email}</p>
                  </div>
                </div>
                <div className="pt-3 border-t border-border">
                  <p className="text-sm text-muted-foreground">Company</p>
                  <p className="font-medium text-foreground">{mockUser.company}</p>
                </div>
              </div>
            </motion.div>

            {/* Testing Playground */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 }}
              className="card-enterprise p-6 mb-8 border-primary/20 bg-primary/5"
            >
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-xs">
                  TEST
                </div>
                <h3 className="text-xl font-bold">Testing Playground</h3>
              </div>
              <p className="text-muted-foreground mb-4 text-sm font-medium">
                Type in the box below to provide **Keystroke Dynamics** output.
                The system captures timing patterns automatically while you type.
              </p>
              <textarea
                placeholder="Start typing here to test biometric capture... (e.g., 'The quick brown fox jumps over the lazy dog')"
                className="w-full h-32 bg-background border-border rounded-xl p-4 focus:ring-2 focus:ring-primary outline-none resize-none text-foreground placeholder:text-muted-foreground/50 transition-all font-medium"
              />
              <div className="flex items-center gap-6 mt-4 p-4 rounded-xl bg-accent/30 border border-border">
                <div className="flex items-center gap-2">
                  <div className={cn("w-3 h-3 rounded-full", isKeystrokeEnrolled ? "bg-success shadow-[0_0_8px_rgba(34,197,94,0.5)]" : "bg-destructive animate-pulse")} />
                  <span className="text-xs font-bold uppercase tracking-wider">
                    Keystroke: {isKeystrokeEnrolled ? 'CAPTURED' : 'INITIALIZING...'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={cn("w-3 h-3 rounded-full", isVoiceEnrolled ? "bg-success shadow-[0_0_8px_rgba(34,197,94,0.5)]" : "bg-destructive animate-pulse")} />
                  <span className="text-xs font-bold uppercase tracking-wider">
                    Voice: {isVoiceEnrolled ? 'CAPTURED' : 'AWAITING INPUT...'}
                  </span>
                </div>
              </div>
            </motion.div>

            {/* Recent Activity */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="card-enterprise p-6"
            >
              <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary" />
                Recent Activity
              </h3>
              <div className="space-y-3">
                {activityLog.map((item, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <div
                      className={cn(
                        'w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5',
                        item.status === 'success' && 'bg-success/10',
                        item.status === 'warning' && 'bg-warning/10',
                        item.status === 'info' && 'bg-primary/10'
                      )}
                    >
                      {item.status === 'success' && (
                        <CheckCircle2 className="w-4 h-4 text-success" />
                      )}
                      {item.status === 'warning' && (
                        <AlertTriangle className="w-4 h-4 text-warning" />
                      )}
                      {item.status === 'info' && (
                        <Activity className="w-4 h-4 text-primary" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground truncate">{item.action}</p>
                      <p className="text-xs text-muted-foreground">{item.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </main>
      <VoiceEnrollmentModal
        isOpen={showEnrollmentModal}
        onComplete={() => {
          setShowEnrollmentModal(false);
          // Voice enrollment complete, scores will update via WebSocket
        }}
      />
      <VoiceVerifier
        checkRequired={voiceCheckRequired}
        onComplete={handleVoiceComplete}
        onCancel={() => setVoiceCheckRequired(false)}
      />
    </div >
  );
};

export default Dashboard;
