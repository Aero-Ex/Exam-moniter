import { io, Socket } from 'socket.io-client';

let socket: Socket | null = null;

export const initSocket = (): Socket => {
  if (!socket) {
    const token = localStorage.getItem('token');
    socket = io('http://localhost:8000', {
      transports: ['websocket', 'polling'],
      autoConnect: false,
      auth: {
        token: token
      },
      query: {
        token: token
      }
    });
  }

  return socket;
};

export const getSocket = (): Socket => {
  if (!socket) {
    return initSocket();
  }
  return socket;
};

export const connectSocket = () => {
  const socket = getSocket();
  if (!socket.connected) {
    socket.connect();
  }
};

export const disconnectSocket = () => {
  if (socket && socket.connected) {
    socket.disconnect();
  }
};
