export const WS_RECONNECT_BASE_MS = 1000;
export const WS_RECONNECT_MAX_MS = 30000;
export const WS_HEARTBEAT_INTERVAL_MS = 25000;
export const MESSAGE_HISTORY_PAGE_SIZE = 50;

export const LOCAL_TESTING = true;

export const getApiBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    return `http://${hostname}:8000`;
  }
  return "http://localhost:8000";
};

export const getWsBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    return `ws://${hostname}:8000`;
  }
  return "ws://localhost:8000";
};
