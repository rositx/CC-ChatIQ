import { create } from 'zustand';
import { Message } from '../types.js';
import { useSessionStore } from './sessionStore.js';

interface MessageState {
  messages: Message[];
  setMessages: (messages: Message[]) => void;
  appendMessage: (message: Message) => void;
  appendStreamToken: (messageId: string, token: string, role?: 'ai' | 'agent') => void;
  mergeMessages: (historicalMessages: Message[]) => void;
}

export const useMessageStore = create<MessageState>((set) => ({
  messages: [],
  setMessages: (messages) => set({ messages }),
  appendMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  appendStreamToken: (messageId, token, role = 'ai') => set((state) => {
    const sessionId = useSessionStore.getState().sessionId || '';
    const idx = state.messages.findIndex(m => m.id === messageId);
    if (idx === -1) {
      const placeholder: Message = {
        id: messageId,
        session_id: sessionId,
        role: role,
        content: token,
        created_at: new Date().toISOString()
      };
      return { messages: [...state.messages, placeholder] };
    }
    const updated = [...state.messages];
    updated[idx] = { ...updated[idx], content: updated[idx].content + token };
    return { messages: updated };
  }),
  mergeMessages: (historicalMessages) => set((state) => {
    const existingIds = new Set(state.messages.map(m => m.id));
    const merged = [...state.messages];
    for (const msg of historicalMessages) {
      if (!existingIds.has(msg.id)) {
        merged.push(msg);
        existingIds.add(msg.id);
      }
    }
    merged.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    return { messages: merged };
  }),
}));

