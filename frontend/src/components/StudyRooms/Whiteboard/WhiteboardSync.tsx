/**
 * WhiteboardSync Component
 *
 * WebSocket synchronization for the collaborative whiteboard.
 * Handles real-time updates between users in the same room.
 */

import axios from 'axios';
import { useEffect, useRef, useCallback } from 'react';

import {
  WhiteboardSyncProps,
  WhiteboardState,
  WhiteboardMessage,
  Stroke,
  Shape,
  TextElement,
  EquationElement,
} from './types';
import { config } from '@/config';

// ============================================================
// Custom Hook for WebSocket Sync
// ============================================================

export interface UseWhiteboardSyncOptions {
  roomId: string;
  onStateChange: (state: WhiteboardState) => void;
  onStrokeAdded: (stroke: Stroke) => void;
  onShapeAdded: (shape: Shape) => void;
  onTextAdded: (text: TextElement) => void;
  onEquationAdded: (equation: EquationElement) => void;
  onClear: () => void;
}

export interface UseWhiteboardSyncReturn {
  isConnected: boolean;
  sendStroke: (stroke: Stroke) => Promise<void>;
  sendShape: (shape: Shape) => Promise<void>;
  sendText: (text: TextElement) => Promise<void>;
  sendEquation: (equation: EquationElement) => Promise<void>;
  sendClear: () => Promise<void>;
  fetchState: () => Promise<WhiteboardState | null>;
}

export const useWhiteboardSync = ({
  roomId,
  onStateChange,
  onStrokeAdded,
  onShapeAdded,
  onTextAdded,
  onEquationAdded,
  onClear,
}: UseWhiteboardSyncOptions): UseWhiteboardSyncReturn => {
  const wsRef = useRef<WebSocket | null>(null);
  const isConnectedRef = useRef(false);

  // Connect to WebSocket
  useEffect(() => {
    const wsUrl = `${config.api.wsURL}/ws/study-rooms/${roomId}/whiteboard`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Whiteboard WebSocket connected');
      isConnectedRef.current = true;
      wsRef.current = ws;
    };

    ws.onmessage = (event) => {
      try {
        const message: WhiteboardMessage = JSON.parse(event.data);
        handleMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Whiteboard WebSocket error:', error);
      isConnectedRef.current = false;
    };

    ws.onclose = () => {
      console.log('Whiteboard WebSocket closed');
      isConnectedRef.current = false;
      wsRef.current = null;
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [roomId]);

  // Handle incoming messages
  const handleMessage = useCallback(
    (message: WhiteboardMessage) => {
      switch (message.type) {
        case 'stroke-added':
          if (message.stroke) {
            onStrokeAdded(message.stroke);
          }
          break;
        case 'shape-added':
          if (message.shape) {
            onShapeAdded(message.shape);
          }
          break;
        case 'text-added':
          if (message.text) {
            onTextAdded(message.text);
          }
          break;
        case 'equation-added':
          if (message.equation) {
            onEquationAdded(message.equation);
          }
          break;
        case 'clear':
          onClear();
          break;
        default:
          console.log('Unknown whiteboard message type:', message.type);
      }
    },
    [onStrokeAdded, onShapeAdded, onTextAdded, onEquationAdded, onClear],
  );

  // Send message via WebSocket
  const sendMessage = useCallback((message: WhiteboardMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  // Fetch initial whiteboard state
  const fetchState = useCallback(async (): Promise<WhiteboardState | null> => {
    try {
      const response = await axios.get<WhiteboardState>(
        `/api/study-rooms/${roomId}/whiteboard/state`,
      );
      onStateChange(response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching whiteboard state:', error);
      return null;
    }
  }, [roomId, onStateChange]);

  // Send stroke to server and broadcast
  const sendStroke = useCallback(
    async (stroke: Stroke): Promise<void> => {
      try {
        await axios.post(`/api/study-rooms/${roomId}/whiteboard/stroke`, stroke);
        sendMessage({ type: 'stroke-added', stroke });
      } catch (error) {
        console.error('Error sending stroke:', error);
      }
    },
    [roomId, sendMessage],
  );

  // Send shape to server and broadcast
  const sendShape = useCallback(
    async (shape: Shape): Promise<void> => {
      try {
        await axios.post(`/api/study-rooms/${roomId}/whiteboard/shape`, shape);
        sendMessage({ type: 'shape-added', shape });
      } catch (error) {
        console.error('Error sending shape:', error);
      }
    },
    [roomId, sendMessage],
  );

  // Send text to server and broadcast
  const sendText = useCallback(
    async (text: TextElement): Promise<void> => {
      try {
        await axios.post(`/api/study-rooms/${roomId}/whiteboard/text`, text);
        sendMessage({ type: 'text-added', text });
      } catch (error) {
        console.error('Error sending text:', error);
      }
    },
    [roomId, sendMessage],
  );

  // Send equation to server and broadcast
  const sendEquation = useCallback(
    async (equation: EquationElement): Promise<void> => {
      try {
        await axios.post(`/api/study-rooms/${roomId}/whiteboard/equation`, equation);
        sendMessage({ type: 'equation-added', equation });
      } catch (error) {
        console.error('Error sending equation:', error);
      }
    },
    [roomId, sendMessage],
  );

  // Send clear command to server and broadcast
  const sendClear = useCallback(async (): Promise<void> => {
    try {
      await axios.post(`/api/study-rooms/${roomId}/whiteboard/clear`);
      sendMessage({ type: 'clear' });
    } catch (error) {
      console.error('Error clearing whiteboard:', error);
    }
  }, [roomId, sendMessage]);

  return {
    isConnected: isConnectedRef.current,
    sendStroke,
    sendShape,
    sendText,
    sendEquation,
    sendClear,
    fetchState,
  };
};

// ============================================================
// WhiteboardSync Component (for declarative usage)
// ============================================================

const WhiteboardSync: React.FC<WhiteboardSyncProps> = ({
  roomId,
  onStrokeAdded,
  onShapeAdded,
  onTextAdded,
  onEquationAdded,
  onClear,
}) => {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const wsUrl = `${config.api.wsURL}/ws/study-rooms/${roomId}/whiteboard`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Whiteboard WebSocket connected');
      wsRef.current = ws;
    };

    ws.onmessage = (event) => {
      try {
        const message: WhiteboardMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'stroke-added':
            if (message.stroke) {onStrokeAdded(message.stroke);}
            break;
          case 'shape-added':
            if (message.shape) {onShapeAdded(message.shape);}
            break;
          case 'text-added':
            if (message.text) {onTextAdded(message.text);}
            break;
          case 'equation-added':
            if (message.equation) {onEquationAdded(message.equation);}
            break;
          case 'clear':
            onClear();
            break;
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Whiteboard WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Whiteboard WebSocket closed');
      wsRef.current = null;
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [roomId, onStrokeAdded, onShapeAdded, onTextAdded, onEquationAdded, onClear]);

  // This component doesn't render anything
  return null;
};

// ============================================================
// Utility Functions
// ============================================================

/**
 * Create empty whiteboard state
 */
export const createEmptyState = (): WhiteboardState => ({
  strokes: [],
  shapes: [],
  texts: [],
  equations: [],
});

/**
 * Serialize whiteboard state to JSON
 */
export const serializeState = (state: WhiteboardState): string => {
  return JSON.stringify(state);
};

/**
 * Deserialize whiteboard state from JSON
 */
export const deserializeState = (json: string): WhiteboardState | null => {
  try {
    const state = JSON.parse(json);
    if (
      Array.isArray(state.strokes) &&
      Array.isArray(state.shapes) &&
      Array.isArray(state.texts) &&
      Array.isArray(state.equations)
    ) {
      return state as WhiteboardState;
    }
    return null;
  } catch {
    return null;
  }
};

export default WhiteboardSync;
