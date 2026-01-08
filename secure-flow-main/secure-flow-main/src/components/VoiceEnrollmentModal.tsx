import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Loader2, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { authApi } from '@/services/api';
import { toast } from 'sonner';

interface VoiceEnrollmentModalProps {
    isOpen: boolean;
    onComplete: () => void;
}

const ENROLLMENT_PHRASES = [
    "My voice is my passport",
    "Security is my priority",
    "I authenticate my identity",
    "Trust through voice verification",
];

const VoiceEnrollmentModal: React.FC<VoiceEnrollmentModalProps> = ({ isOpen, onComplete }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isComplete, setIsComplete] = useState(false);
    const [countdown, setCountdown] = useState<number | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const phrase = ENROLLMENT_PHRASES[Math.floor(Math.random() * ENROLLMENT_PHRASES.length)];

    // Auto-start recording logic
    React.useEffect(() => {
        if (isOpen && !isRecording && !isProcessing && !isComplete && countdown === null) {
            setCountdown(3);
        }
    }, [isOpen]);

    React.useEffect(() => {
        if (countdown !== null && countdown > 0) {
            const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
            return () => clearTimeout(timer);
        } else if (countdown === 0) {
            setCountdown(null);
            startRecording();
        }
    }, [countdown]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream);
            audioChunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorderRef.current.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
                await enrollVoice(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);

            // Auto stop after 4 seconds
            setTimeout(() => {
                if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
                    mediaRecorderRef.current.stop();
                    setIsRecording(false);
                    setIsProcessing(true);
                }
            }, 4000);

        } catch (error) {
            console.error('Error accessing microphone:', error);
            toast.error('Could not access microphone');
            setIsProcessing(false);
        }
    };

    const enrollVoice = async (audioBlob: Blob) => {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'enrollment.wav');

            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'}/auth/voice/enroll`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${sessionStorage.getItem('token')}`
                },
                body: formData
            });

            if (response.ok) {
                setIsComplete(true);
                toast.success('Voice baseline captured');
                setTimeout(() => {
                    onComplete();
                }, 1500);
            } else {
                toast.error('Enrollment failed. Please try again.');
                setIsProcessing(false);
            }
        } catch (error) {
            console.error('Enrollment error:', error);
            toast.error('Error during enrollment');
            setIsProcessing(false);
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    className="bg-background rounded-2xl p-8 w-full max-w-md shadow-2xl border border-border"
                >
                    <div className="text-center">
                        <h2 className="text-2xl font-bold mb-2">Securing your session</h2>
                        <p className="text-muted-foreground mb-6">Please say the following phrase once</p>

                        <div className="bg-accent/50 rounded-xl p-6 mb-6">
                            <p className="text-xl font-medium text-primary">"{phrase}"</p>
                        </div>

                        {!isComplete && (
                            <>
                                {countdown !== null && (
                                    <div className="flex flex-col items-center mb-6">
                                        <div className="text-6xl font-black text-primary animate-bounce">
                                            {countdown}
                                        </div>
                                        <p className="text-muted-foreground mt-2 font-medium">Get ready...</p>
                                    </div>
                                )}

                                {!isRecording && !isProcessing && countdown === null && (
                                    <Button
                                        onClick={startRecording}
                                        size="lg"
                                        className="rounded-full w-20 h-20 p-0 hover:scale-105 transition-transform"
                                    >
                                        <Mic className="w-10 h-10" />
                                    </Button>
                                )}

                                {isRecording && (
                                    <div className="flex flex-col items-center">
                                        <div className="w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mb-4 relative">
                                            <motion.div
                                                animate={{ scale: [1, 1.2, 1] }}
                                                transition={{ repeat: Infinity, duration: 1.5 }}
                                                className="absolute inset-0 bg-primary/20 rounded-full"
                                            />
                                            <Mic className="w-12 h-12 text-primary z-10" />
                                        </div>
                                        <p className="text-primary font-medium animate-pulse">Recording...</p>
                                    </div>
                                )}

                                {isProcessing && (
                                    <div className="flex flex-col items-center">
                                        <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
                                        <p className="text-muted-foreground">Processing voice sample...</p>
                                    </div>
                                )}
                            </>
                        )}

                        {isComplete && (
                            <div className="flex flex-col items-center">
                                <CheckCircle2 className="w-16 h-16 text-success mb-4" />
                                <p className="text-lg font-medium text-success">Baseline captured!</p>
                            </div>
                        )}
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};

export default VoiceEnrollmentModal;
