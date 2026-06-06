import React, { useRef, useEffect } from "react";
import { useMessageStore } from "@opendesk/core";
import { MessageBubble } from "./MessageBubble";

const StreamingAutoScroller: React.FC<{ containerRef: React.RefObject<HTMLDivElement> }> = ({ containerRef }) => {
  // This leaf component subscribes to token appends, isolating all updates
  const streamingTextLength = useMessageStore(
    (state) => state.messages[state.messages.length - 1]?.content.length || 0
  );
  
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    
    // 45px boundary threshold allows for padding variance
    const isPinnedToBottom = el.scrollHeight - el.scrollTop - el.clientHeight <= 45;
    
    if (isPinnedToBottom) {
      el.scrollTop = el.scrollHeight;
    }
  }, [streamingTextLength, containerRef]);

  return null;
};

export const MessageStream: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Extract strictly the list of unique message tracking IDs to protect memoization loops
  const messageIds = useMessageStore(
    (state) => state.messages.map((m) => m.id),
    (prev, next) => prev.length === next.length && prev.every((v, i) => v === next[i])
  );

  return (
    <div 
      ref={containerRef} 
      style={{ overflowY: "auto", height: "100%", padding: "16px", display: "flex", flexDirection: "column" }}
    >
      {messageIds.map((id) => (
        <MessageBubble key={id} messageId={id} />
      ))}
      <StreamingAutoScroller containerRef={containerRef} />
    </div>
  );
};
