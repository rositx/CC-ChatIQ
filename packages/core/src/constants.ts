export const WS_RECONNECT_BASE_MS = 1000;
export const WS_RECONNECT_MAX_MS = 30000;
export const WS_HEARTBEAT_INTERVAL_MS = 25000;
export const MESSAGE_HISTORY_PAGE_SIZE = 50;

export const LOCAL_TESTING = true;

export const getApiBaseUrl = (): string => {
  return LOCAL_TESTING ? "http://localhost:8000" : "";
};

export const getWsBaseUrl = (): string => {
  if (LOCAL_TESTING) {
    return "ws://localhost:8000";
  }
  const protocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = typeof window !== "undefined" ? window.location.host : "localhost:8000";
  return `${protocol}//${host}`;
};
