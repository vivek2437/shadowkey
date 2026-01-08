import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, X, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { authApi } from '@/services/api';
import { toast } from 'sonner';

interface VoiceVerifierProps {
    checkRequired: boolean;
    onComplete: (success: boolean) => void;
    onCancel: () => void;
}

const VoiceVerifier: React.FC<VoiceVerifierProps> = ({ checkRequired, onComplete, onCancel }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isVerifying, setIsVerifying] = useState(false);
    const [status, setStatus] = useState<'idle' | 'recording' | 'verifying' | 'success' | 'failed'>('idle');
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

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
                verifyVoice(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
            setStatus('recording');

            // Auto stop after 3 seconds for short sample
            setTimeout(() => {
                if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
                    stopRecording();
                }
            }, 3000);

        } catch (error) {
            console.error('Error accessing microphone:', error);
            toast.error('Could not access microphone');
            setStatus('failed');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            setStatus('verifying');
        }
    };

    const verifyVoice = async (audioBlob: Blob) => {
        setIsVerifying(true);
        try {
            const response = await authApi.verifyVoice(audioBlob);
            if (response.verified) {
                setStatus('success');
                toast.success('Voice verified successfully');
                setTimeout(() => onComplete(true), 1500);
            } else {
                setStatus('failed');
                toast.error('Voice verification failed. Please try again.');
                // Allow retry
            }
        } catch (error) {
            console.error('Verification error:', error);
            setStatus('failed');
            toast.error('Error verifying voice.');
        } finally {
            setIsVerifying(false);
        }
    };

    return (
        <AnimatePresence>
            {checkRequired && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
                >
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.9, opacity: 0 }}
                        className="bg-background rounded-2xl p-8 w-full max-w-md shadow-2xl border border-border"
                    >
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold flex items-center gap-2">
                                <Mic className="w-5 h-5 text-primary" />
                                Voice Verification Required
                            </h2>
                            <Button variant="ghost" size="icon" onClick={onCancel}>
                                <X className="w-5 h-5" />
                            </Button>
                        </div>

                        <div className="flex flex-col items-center justify-center py-8">
                            {status === 'idle' && (
                                <div className="text-center">
                                    <p className="text-muted-foreground mb-6">Please speak the passphrase to verify your identity.</p>
                                    <Button onClick={startRecording} size="lg" className="rounded-full w-16 h-16 p-0 hover:scale-105 transition-transform">
                                        <Mic className="w-8 h-8" />
                                    </Button>
                                </div>
                            )}

                            {status === 'recording' && (
                                <div className="text-center">
                                    <div className="w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mb-4 relative">
                                        <motion.div
                                            animate={{ scale: [1, 1.2, 1] }}
                                            transition={{ repeat: Infinity, duration: 1.5 }}
                                            className="absolute inset-0 bg-primary/20 rounded-full"
                                        />
                                        <Mic className="w-10 h-10 text-primary z-10" />
                                    </div>
                                    <p className="text-primary font-medium animate-pulse">Listening...</p>
                                </div>
                            )}

                            {status === 'verifying' && (
                                <div className="text-center">
                                    <Loader2 className="w-12 h-12 text-primary animate-spin mb-4 mx-auto" />
                                    <p className="text-muted-foreground">Verifying voice biometric...</p>
                                </div>
                            )}

                            {status === 'success' && (
                                <div className="text-center">
                                    <CheckCircle2 className="w-16 h-16 text-success mx-auto mb-4" />
                                    <p className="text-lg font-medium text-success">Verified</p>
                                </div>
                            )}

                            {status === 'failed' && (
                                <div className="text-center">
                                    <AlertTriangle className="w-16 h-16 text-destructive mx-auto mb-4" />
                                    <p className="text-lg font-medium text-destructive mb-4">Verification Failed</p>
                                    <Button onClick={() => setStatus('idle')}>Try Again</Button>
                                </div>
                            )}
                        </div>

                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default VoiceVerifier;
