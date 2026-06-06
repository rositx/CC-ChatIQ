import React, { useState } from "react";
import { StyleSheet, View, Text, TextInput, TouchableOpacity, FlatList, KeyboardAvoidingView, Platform } from "react-native";
import { useSupportChat } from "../hooks/useSupportChat";

interface SupportChatProps {
  tenantId: string;
  sessionId: string;
  websocketUrl: string;
  token: string;
}

export const SupportChat: React.FC<SupportChatProps> = ({ tenantId, sessionId, websocketUrl, token }) => {
  const { messages, isConnected, sendTextMessage, escalateToAgent } = useSupportChat({
    tenantId,
    sessionId,
    websocketUrl,
    token,
  });
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (input.trim()) {
      sendTextMessage(input);
      setInput("");
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Support Chat</Text>
        <Text style={[styles.status, isConnected ? styles.online : styles.offline]}>
          {isConnected ? "Connected" : "Reconnecting..."}
        </Text>
      </View>

      <FlatList
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={[styles.msgBubble, item.role === "customer" ? styles.customerMsg : styles.agentMsg]}>
            <Text style={styles.msgText}>{item.content}</Text>
          </View>
        )}
        contentContainerStyle={styles.messageStream}
      />

      <View style={styles.inputArea}>
        <TextInput
          style={styles.textInput}
          value={input}
          onChangeText={setInput}
          placeholder="Type your message..."
        />
        <TouchableOpacity style={styles.sendBtn} onPress={handleSend}>
          <Text style={styles.sendBtnText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  header: { padding: 15, borderBottomWidth: 1, borderBottomColor: "#eee", flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  headerTitle: { fontWeight: "bold", fontSize: 16 },
  status: { fontSize: 12 },
  online: { color: "green" },
  offline: { color: "red" },
  messageStream: { padding: 15 },
  msgBubble: { padding: 10, borderRadius: 8, marginVertical: 5, maxWidth: "80%" },
  customerMsg: { alignSelf: "flex-end", backgroundColor: "#4F46E5" },
  agentMsg: { alignSelf: "flex-start", backgroundColor: "#E5E7EB" },
  msgText: { color: "#000" },
  inputArea: { flexDirection: "row", padding: 10, borderTopWidth: 1, borderTopColor: "#eee" },
  textInput: { flex: 1, borderWidth: 1, borderColor: "#ccc", borderRadius: 4, paddingHorizontal: 10, marginRight: 10 },
  sendBtn: { backgroundColor: "#4F46E5", padding: 10, borderRadius: 4, justifyContent: "center" },
  sendBtnText: { color: "#fff", fontWeight: "bold" },
});
