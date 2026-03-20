import { Client } from "@stomp/stompjs";
import SockJS from "sockjs-client";

const SOCKET_URL = "http://localhost:8080/ws";

let stompClient = null;
let isConnected = false;
let messageQueue = [];

export const connect = (onMessageReceived) => {
  if (stompClient && isConnected && stompClient.connected) {
    console.log("WebSocket already connected");
    return;
  }

  // Clean up any existing connection
  if (stompClient) {
    stompClient.deactivate();
  }

  const client = new Client({
    webSocketFactory: () => new SockJS(SOCKET_URL),
    onConnect: () => {
      console.log("WebSocket Connected!");
      // Wait a moment to ensure the connection is fully established
      setTimeout(() => {
        isConnected = true;
        console.log("WebSocket ready for messages");

        // Subscribe to the public topic
        client.subscribe("/topic/edits", (message) => {
          onMessageReceived(message.body);
        });

        // Process any queued messages
        while (messageQueue.length > 0) {
          const { sessionId, content } = messageQueue.shift();
          sendMessageInternal(sessionId, content);
        }
      }, 100); // Small delay to ensure STOMP is fully ready
    },
    onDisconnect: () => {
      console.log("WebSocket Disconnected!");
      isConnected = false;
    },
    onStompError: (frame) => {
      console.error("Broker reported error: " + frame.headers["message"]);
      console.error("Additional details: " + frame.body);
      isConnected = false;
    },
    reconnectDelay: 5000,
    heartbeatIncoming: 4000,
    heartbeatOutgoing: 4000,
  });

  client.activate();
  stompClient = client;
  isConnected = false; // Reset state
};

const sendMessageInternal = (sessionId, content) => {
  if (stompClient && isConnected && stompClient.connected) {
    try {
      stompClient.publish({
        destination: "/app/spec/edit",
        body: JSON.stringify({ sessionId, content }),
      });
      console.log("Message sent successfully");
      return true;
    } catch (error) {
      console.error("Failed to send message:", error);
      isConnected = false; // Reset connection state on error
      return false;
    }
  }
  return false;
};

export const sendMessage = (sessionId, content) => {
  if (!sessionId || !content) {
    console.warn("Cannot send message: missing sessionId or content");
    return;
  }

  if (!stompClient) {
    console.warn("STOMP client not initialized, queuing message");
    messageQueue.push({ sessionId, content });
    return;
  }

  const sent = sendMessageInternal(sessionId, content);
  if (!sent) {
    // Queue the message if not connected
    console.log("WebSocket not ready, queuing message. Connection state:", {
      hasClient: !!stompClient,
      isConnected: isConnected,
      clientConnected: stompClient ? stompClient.connected : false,
    });
    messageQueue.push({ sessionId, content });

    // Remove old messages from queue to prevent memory issues
    if (messageQueue.length > 10) {
      messageQueue.shift();
    }
  }
};

export const isWebSocketConnected = () => {
  return isConnected && stompClient && stompClient.connected;
};

export const disconnect = () => {
  if (stompClient) {
    isConnected = false;
    messageQueue = []; // Clear message queue
    stompClient.deactivate();
    stompClient = null;
    console.log("WebSocket Disconnected!");
  }
};
