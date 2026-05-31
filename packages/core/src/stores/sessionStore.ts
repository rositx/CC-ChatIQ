import { create } from 'zustand';

interface SessionState {
  token: string | null;
  sessionId: string | null;
  connectionStatus: 'connecting' | 'connected' | 'reconnecting' | 'disconnected';
  setSession: (token: string, sessionId: string) => void;
  setConnectionStatus: (status: 'connecting' | 'connected' | 'reconnecting' | 'disconnected') => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  token: null,
  sessionId: null,
  connectionStatus: 'disconnected',
  setSession: (token, sessionId) => set({ token, sessionId }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
}));
