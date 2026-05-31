import React, { useRef, useEffect } from "react";
import { useMessageStore } from "@opendesk/core";
import { MessageBubble } from "./MessageBubble";

export const MessageStream: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Extract strictly the list of unique message tracking IDs to protect memoization loops
  const messageIds = useMessageStore(
    (state) => state.messages.map((m) => m.id),
    (prev, next) => prev.length === next.length && prev.every((v, i) => v === next[i])
  );

  // Monitor the dynamic text payload bounds of the absolute bottom array item
  const streamingTextLength = useMessageStore(
    (state) => state.messages[state.messages.length - 1]?.content.length || 0
  );

  // Auto-scroll pinning execution engine
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    
    // 30px boundary threshold allows for padding variance
    const isPinnedToBottom = el.scrollHeight - el.scrollTop - el.clientHeight <= 30;
    
    if (isPinnedToBottom) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messageIds, streamingTextLength]); // Triggers on new cards AND expanding text boundaries

  return (
    <div 
      ref={containerRef} 
      style={{ overflowY: "auto", height: "100%", padding: "16px", display: "flex", flexDirection: "column" }}
    >
      {messageIds.map((id) => (
        <MessageBubble key={id} messageId={id} />
      ))}
    </div>
  );
};
