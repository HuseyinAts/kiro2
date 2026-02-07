/**
 * Multi-Agent Blackboard API Servisi
 * Teknofest 2025 - Eğitim Eylemci Projesi
 */

import config from '../config';
import { ApiResponse } from '../types/revolutionary';

const API_BASE_URL = config.api.baseURL;

export interface WriteDataRequest {
  key: string;
  value: any;
  ttl_seconds?: number;
  metadata?: Record<string, any>;
  priority?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface CoordinationRequest {
  target_agents: string[];
  coordination_type: string;
  parameters: Record<string, any>;
  timeout_seconds?: number;
}

export interface CoordinationResponse {
  coordination_id: string;
  response_data: Record<string, any>;
}

export interface BlackboardMetrics {
  total_writes: number;
  total_reads: number;
  total_notifications: number;
  active_subscriptions: number;
  coordination_requests: number;
  average_response_time: number;
  registered_agents: number;
  active_data_entries: number;
  event_history_size: number;
  websocket_connections: number;
}

export interface AgentStatus {
  [agentName: string]: {
    status: string;
    subscriptions: number;
    last_activity: string | null;
  };
}

export interface BlackboardEvent {
  event_id: string;
  event_type: string;
  key: string;
  value: any;
  source_agent: string;
  target_agents: string[] | null;
  priority: number;
  timestamp: string;
  metadata: Record<string, any> | null;
  requires_response: boolean;
  correlation_id: string | null;
}

class MultiAgentService {
  private baseUrl: string;
  private websocket: WebSocket | null = null;
  private eventListeners: Map<string, (event: BlackboardEvent) => void> = new Map();

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1/multi-agent`;
  }

  /**
   * Blackboard'a veri yaz
   */
  async writeData(request: WriteDataRequest): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/write`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Write data error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Veri yazma hatası',
      };
    }
  }

  /**
   * Blackboard'dan veri oku
   */
  async readData(key: string): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/read/${encodeURIComponent(key)}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Read data error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Veri okuma hatası',
      };
    }
  }

  /**
   * Blackboard'dan veri sil
   */
  async deleteData(key: string): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/delete/${encodeURIComponent(key)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Delete data error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Veri silme hatası',
      };
    }
  }

  /**
   * Agent koordinasyonu talep et
   */
  async requestCoordination(request: CoordinationRequest): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/coordination/request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Coordination request error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Koordinasyon talebi hatası',
      };
    }
  }

  /**
   * Koordinasyon talebine yanıt ver
   */
  async respondCoordination(response: CoordinationResponse): Promise<ApiResponse<any>> {
    try {
      const apiResponse = await fetch(`${this.baseUrl}/coordination/respond`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(response),
      });

      if (!apiResponse.ok) {
        throw new Error(`HTTP error! status: ${apiResponse.status}`);
      }

      const data = await apiResponse.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Coordination response error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Koordinasyon yanıtı hatası',
      };
    }
  }

  /**
   * Blackboard metriklerini al
   */
  async getMetrics(): Promise<ApiResponse<BlackboardMetrics | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/metrics`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Get metrics error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Metrik alma hatası',
      };
    }
  }

  /**
   * Agent durumlarını al
   */
  async getAgentStatus(): Promise<ApiResponse<AgentStatus | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Get agent status error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Agent durumu alma hatası',
      };
    }
  }

  /**
   * Olay geçmişini al
   */
  async getEventHistory(
    limit: number = 100,
    eventType?: string,
    agentName?: string,
  ): Promise<ApiResponse<BlackboardEvent[] | null>> {
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
      });

      if (eventType) {
        params.append('event_type', eventType);
      }

      if (agentName) {
        params.append('agent_name', agentName);
      }

      const response = await fetch(`${this.baseUrl}/events/history?${params}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Get event history error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Olay geçmişi alma hatası',
      };
    }
  }

  /**
   * WebSocket bağlantısı kur
   */
  connectWebSocket(clientId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/api/v1/multi-agent/ws/${clientId}`;
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
          // Multi-Agent WebSocket connected
          resolve();
        };

        this.websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'blackboard_event') {
              const blackboardEvent: BlackboardEvent = data.event;

              // Event listener'ları çağır
              this.eventListeners.forEach((listener) => {
                listener(blackboardEvent);
              });
            }
          } catch (error) {
            console.error('WebSocket message parse error:', error);
          }
        };

        this.websocket.onerror = (error) => {
          console.error('Multi-Agent WebSocket error:', error);
          reject(error);
        };

        this.websocket.onclose = () => {
          // Multi-Agent WebSocket disconnected
          this.websocket = null;
        };

        // Ping/pong için heartbeat
        setInterval(() => {
          if (this.websocket?.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000); // 30 saniyede bir ping

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * WebSocket bağlantısını kapat
   */
  disconnectWebSocket(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.eventListeners.clear();
  }

  /**
   * Blackboard event listener ekle
   */
  addEventListener(id: string, listener: (event: BlackboardEvent) => void): void {
    this.eventListeners.set(id, listener);
  }

  /**
   * Blackboard event listener kaldır
   */
  removeEventListener(id: string): void {
    this.eventListeners.delete(id);
  }

  /**
   * Sistem sağlık kontrolü
   */
  async healthCheck(): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.status === 'healthy',
        data: data,
        message: data.status === 'healthy' ? 'Sistem sağlıklı' : 'Sistem sağlıksız',
      };
    } catch (error) {
      console.error('Health check error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Sağlık kontrolü hatası',
      };
    }
  }
}

// Singleton instance
const multiAgentService = new MultiAgentService();

export default multiAgentService;