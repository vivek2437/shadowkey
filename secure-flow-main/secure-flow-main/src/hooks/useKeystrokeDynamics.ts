import { useEffect, useRef } from 'react';
import { authApi } from '@/services/api';

interface KeyEventPayload {
    key: string;
    event_type: 'keydown' | 'keyup';
    timestamp: number;
}

export const useKeystrokeDynamics = () => {
    const bufferRef = useRef<KeyEventPayload[]>([]);
    const processingRef = useRef(false);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Ignore sensitive keys if needed, or capturing everything for auth
            // Usually passwords are redacted or not captured for strict privacy, 
            // but behavioral auth needs the timing. 
            // ShadowKey likely wants the timing of everything.
            // We will capture timing and obfuscate the key char if inside password field?
            // For now, capturing all simple keys.

            const payload: KeyEventPayload = {
                key: e.key,
                event_type: 'keydown',
                timestamp: Date.now(),
            };
            bufferRef.current.push(payload);
            console.log('[ShadowKey] Keystroke captured:', e.key, 'Buffer size:', bufferRef.current.length);
        };

        const handleKeyUp = (e: KeyboardEvent) => {
            const payload: KeyEventPayload = {
                key: e.key,
                event_type: 'keyup',
                timestamp: Date.now(),
            };
            bufferRef.current.push(payload);
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);

        const intervalId = setInterval(async () => {
            if (bufferRef.current.length > 0 && !processingRef.current) {
                const token = sessionStorage.getItem('token');
                const sessionId = sessionStorage.getItem('session_id');

                console.log('[ShadowKey] Checking auth - token:', !!token, 'sessionId:', !!sessionId);

                if (!token && !sessionId) {
                    console.log('[ShadowKey] Not logged in, clearing buffer');
                    bufferRef.current = [];
                    return;
                }

                processingRef.current = true;
                const batch = [...bufferRef.current];
                bufferRef.current = [];

                console.log('[ShadowKey] Sending batch of', batch.length, 'keystrokes...');
                try {
                    await authApi.sendKeystrokeData(batch);
                    console.log('[ShadowKey] ✓ Sent batch of', batch.length, 'keystrokes successfully');
                } catch (error: any) {
                    console.error('[ShadowKey] ✗ Failed to send keystroke data:', error?.message || error);
                } finally {
                    processingRef.current = false;
                }
            }
        }, 2000);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
            clearInterval(intervalId);
        };
    }, []);
};
