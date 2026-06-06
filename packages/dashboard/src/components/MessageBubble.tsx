import React from "react";
import { useMessageStore } from "@opendesk/core";

export const MessageBubble: React.FC<{ messageId: string }> = React.memo(({ messageId }) => {
  const message = useMessageStore(
    (state) => state.messages.find((m) => m.id === messageId),
    (prev, next) => prev?.content === next?.content && prev?.role === next?.role
  );
  if (!message) return null;

  const isUser = message.role === "customer";
  const bubbleStyle: React.CSSProperties = {
    alignSelf: isUser ? "flex-end" : "flex-start",
    backgroundColor: isUser ? "#2563eb" : "#1e293b",
    color: "#ffffff",
    padding: "8px 12px",
    borderRadius: "8px",
    marginBottom: "8px",
    maxWidth: "70%",
    wordBreak: "break-word",
  };

  return <div style={bubbleStyle}>{message.content}</div>;
});
