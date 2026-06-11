import { useState, useEffect, useRef } from 'react';
import { getApiBaseUrl, GHIResponse } from '../api';

export interface TelemetryData extends GHIResponse {
  wazuh_status: string;
  splunk_status: string;
  wazuh_agent_status: any;
  timestamp: string;
  roi_metrics?: {
    base_manual_hours: number;
    automated_hours: number;
    hours_saved: number;
    revenue_protected: number;
    total_controls: number;
    automated_controls: number;
  };
}

export function useTelemetryWebSocket(orgId: string) {
  const [data, setData] = useState<TelemetryData | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!orgId) return;

    // Construct WebSocket URL dynamically from API base URL configuration
    const apiBase = getApiBaseUrl();
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl = '';
    if (!apiBase || apiBase.startsWith('/')) {
      wsUrl = `${wsProtocol}//${window.location.host}/ws/telemetry?org_id=${orgId}`;
    } else {
      wsUrl = apiBase.replace(/^http/, 'ws') + `/ws/telemetry?org_id=${orgId}`;
    }

    let reconnectTimer: any;
    
    function connect() {
      console.log(`[WebSocket] Connecting to ${wsUrl}`);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WebSocket] Telemetry connection established');
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          if (parsed.error) {
            console.error('[WebSocket] Server error detail:', parsed.error);
          } else {
            setData(parsed);
          }
        } catch (err) {
          console.error('[WebSocket] Telemetry parse failed:', err);
        }
      };

      ws.onclose = (event) => {
        console.log(`[WebSocket] Connection terminated: code=${event.code}`);
        setConnected(false);
        // Automatic retry loop after 4 seconds
        reconnectTimer = setTimeout(() => {
          connect();
        }, 4000);
      };

      ws.onerror = (err) => {
        console.error('[WebSocket] Socket communication failure:', err);
        ws.close();
      };
    }

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      clearTimeout(reconnectTimer);
    };
  }, [orgId]);

  return { data, connected };
}
