export interface Message {
  id: string;
  session_id: string;
  role: 'customer' | 'ai' | 'agent' | 'system';
  content: string;
  created_at: string;
}
