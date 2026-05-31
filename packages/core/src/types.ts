export interface Message {
  id: string;
  session_id: string;
  role: "customer" | "agent" | "system" | "ai";
  content: string;
  created_at: string;
}
