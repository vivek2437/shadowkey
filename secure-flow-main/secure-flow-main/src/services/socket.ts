type WebSocketMessageHandler = (data: any) => void;
type ConnectionStateListener = (isConnected: boolean) => void;

class WebSocketService {
    private ws: WebSocket | null = null;
    private url: string;
    private listeners: Set<WebSocketMessageHandler> = new Set();
    private connectionListeners: Set<ConnectionStateListener> = new Set();
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 5;
    private reconnectBaseDelay: number = 1000;
    private isConnecting: boolean = false;
    private shouldReconnect: boolean = true;

    constructor() {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        // Replace http/https with ws/wss
        this.url = baseUrl.replace(/^http/, 'ws') + '/auth/continuous';
    }

    public connect() {
        if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) return;

        this.isConnecting = true;
        this.shouldReconnect = true;

        try {
            const sessionId = sessionStorage.getItem('session_id');
            const token = sessionStorage.getItem('token');

            // Prefer session_id as per requirements, fallback to token if needed or just use session_id
            const queryParams = new URLSearchParams();
            if (sessionId) queryParams.append('session_id', sessionId);
            if (token) queryParams.append('token', token);

            const wsUrl = `${this.url}?${queryParams.toString()}`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('ShadowKey WebSocket Connected');
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.notifyConnectionListeners(true);
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.notifyListeners(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message', e);
                }
            };

            this.ws.onclose = () => {
                console.log('ShadowKey WebSocket Closed');
                this.isConnecting = false;
                this.notifyConnectionListeners(false);
                if (this.shouldReconnect) {
                    this.handleReconnect();
                }
            };

            this.ws.onerror = (error) => {
                console.error('ShadowKey WebSocket Error', error);
                this.ws?.close();
            };

        } catch (error) {
            console.error('WebSocket connection failed', error);
            this.isConnecting = false;
            this.notifyConnectionListeners(false);
            this.handleReconnect();
        }
    }

    public disconnect() {
        this.shouldReconnect = false;
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    public subscribe(handler: WebSocketMessageHandler) {
        this.listeners.add(handler);
        return () => this.listeners.delete(handler);
    }

    public onConnectionChange(handler: ConnectionStateListener) {
        this.connectionListeners.add(handler);
        // Immediately notify current state
        handler(this.ws?.readyState === WebSocket.OPEN);
        return () => this.connectionListeners.delete(handler);
    }

    private notifyListeners(data: any) {
        this.listeners.forEach((listener) => listener(data));
    }

    private notifyConnectionListeners(isConnected: boolean) {
        this.connectionListeners.forEach((listener) => listener(isConnected));
    }

    private handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnect attempts reached');
            return;
        }

        const delay = this.reconnectBaseDelay * Math.pow(2, this.reconnectAttempts);
        this.reconnectAttempts++;
        console.log(`Reconnecting in ${delay}ms...`);

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    public sendMessage(type: string, payload: any) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, payload }));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }
}

export const socketService = new WebSocketService();
