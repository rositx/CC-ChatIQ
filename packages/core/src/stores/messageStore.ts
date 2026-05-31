import { create } from "zustand";
import { Message } from "../types.js";

interface MessageState {
  messages: Message[];
  setMessages: (msgs: Message[]) => void;
  appendMessage: (msg: Message) => void;
  appendToken: (messageId: string, token: string, role?: "ai" | "agent") => void;
  mergeMessages: (historicalMessages: Message[]) => void;
}

export const useMessageStore = create<MessageState>((set) => ({
  messages: [],
  setMessages: (msgs) => set({ messages: msgs }),
  appendMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  
  appendToken: (messageId, token, role = "ai") =>
    set((state) => {
      const existingIndex = state.messages.findIndex((m) => m.id === messageId);

      if (existingIndex === -1) {
        const placeholderShell: Message = {
          id: messageId,
          session_id: "", 
          role: role,
          content: token,
          created_at: new Date().toISOString(),
        };
        return { messages: [...state.messages, placeholderShell] };
      }

      const updated = [...state.messages];
      updated[existingIndex] = {
        ...updated[existingIndex],
        content: updated[existingIndex].content + token,
      };
      return { messages: updated };
    }),

  mergeMessages: (historicalMessages) =>
    set((state) => {
      const existingIds = new Set(state.messages.map((m) => m.id));
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
