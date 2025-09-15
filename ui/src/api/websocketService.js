import { Client } from '@stomp/stompjs';
import SockJS from 'sockjs-client';

const SOCKET_URL = 'http://localhost:8080/ws';

let stompClient = null;

export const connect = (onMessageReceived) => {
    const client = new Client({
        webSocketFactory: () => new SockJS(SOCKET_URL),
        onConnect: () => {
            console.log('WebSocket Connected!');
            // Subscribe to the public topic
            client.subscribe('/topic/edits', (message) => {
                onMessageReceived(message.body);
            });
        },
        onStompError: (frame) => {
            console.error('Broker reported error: ' + frame.headers['message']);
            console.error('Additional details: ' + frame.body);
        },
    });

    client.activate();
    stompClient = client;
};

export const sendMessage = (sessionId, content) => {
    if (stompClient && stompClient.active) {
        stompClient.publish({
            destination: '/app/spec/edit',
            body: JSON.stringify({ sessionId, content }),
        });
    } else {
        console.error('Cannot send message, STOMP client is not active.');
    }
};

export const disconnect = () => {
    if (stompClient) {
        stompClient.deactivate();
        console.log('WebSocket Disconnected!');
    }
};