import { create } from 'zustand';

export interface SessionInfo {
  id: string;
  trigger: string;
  escalated_at: string | null;
}

interface QueueState {
  queue: SessionInfo[];
  activeSessionId: string | null;
  setQueue: (q: SessionInfo[]) => void;
  addQueueItem: (item: SessionInfo) => void;
  removeQueueItem: (id: string) => void;
  setActiveSessionId: (id: string | null) => void;
}

export const useQueueStore = create<QueueState>((set) => ({
  queue: [],
  activeSessionId: null,
  setQueue: (q) => set({ queue: q }),
  addQueueItem: (item) => set((state) => ({ queue: [...state.queue.filter(x => x.id !== item.id), item] })),
  removeQueueItem: (id) => set((state) => ({ queue: state.queue.filter((x) => x.id !== id) })),
  setActiveSessionId: (id) => set({ activeSessionId: id }),
}));
