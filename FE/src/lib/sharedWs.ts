import { Client } from '@stomp/stompjs';
import type { IMessage, StompSubscription } from '@stomp/stompjs';

type Candle = { time: number; open: number; high: number; low: number; close: number; symbol?: string; volume?: number };

type Listener = (c: Candle) => void;

const WS_URL = 'ws://localhost/ws';

class SharedWs {
  private client: Client | null = null;
  // listeners keyed by "SYMBOL:INTERVAL" (e.g. "BTCUSDT:1m")
  private listeners: Map<string, Set<Listener>> = new Map();
  // track STOMP subscriptions
  private stompSubscriptions: Map<string, StompSubscription> = new Map();
  // debug flag to enable verbose logging for message dispatch issues
  private debug = false;

  constructor() {
    this.initClient();
  }

  private initClient() {
    this.client = new Client({
      brokerURL: WS_URL,
      reconnectDelay: 5000,
      heartbeatIncoming: 4000,
      heartbeatOutgoing: 4000,
      debug: (str) => {
        if (this.debug) {
          console.debug('[STOMP]', str);
        }
      },
      onConnect: () => {
        console.log('[sharedWs] STOMP connected');
        // Re-subscribe to all existing topics
        for (const topic of this.listeners.keys()) {
          this.subscribeToTopic(topic);
        }
      },
      onDisconnect: () => {
        console.log('[sharedWs] STOMP disconnected');
      },
      onStompError: (frame) => {
        console.error('[sharedWs] STOMP error:', frame.headers['message']);
      },
    });
  }

  ensureConnected() {
    if (this.client && !this.client.active) {
      this.client.activate();
    }
  }

  // enable or disable debug logging at runtime
  public setDebug(enabled: boolean) {
    this.debug = !!enabled;
  }

  private subscribeToTopic(topic: string) {
    if (!this.client || !this.client.connected) return;
    if (this.stompSubscriptions.has(topic)) return;

    const [symbol, interval] = topic.split(':');
    // BE broadcasts to /topic/candle.{SYMBOL}.{INTERVAL}
    const destination = `/topic/candle.${symbol}.${interval}`;

    const subscription = this.client.subscribe(destination, (message: IMessage) => {
      this.handleMessage(message.body, topic);
    });

    this.stompSubscriptions.set(topic, subscription);
    if (this.debug) {
      console.debug('[sharedWs] Subscribed to', destination);
    }
  }

  private unsubscribeFromTopic(topic: string) {
    const subscription = this.stompSubscriptions.get(topic);
    if (subscription) {
      subscription.unsubscribe();
      this.stompSubscriptions.delete(topic);
    }
  }

  subscribe(symbol: string, cb: Listener, interval: string = '1m') {
    const normalized = String(symbol).toUpperCase();
    const topic = `${normalized}:${interval}`;
    const set = this.listeners.get(topic) ?? new Set();
    set.add(cb);
    this.listeners.set(topic, set);

    this.ensureConnected();

    // Subscribe to STOMP topic if connected
    if (this.client?.connected) {
      this.subscribeToTopic(topic);
    }

    return () => this.unsubscribeTopic(topic, cb);
  }

  // unsubscribe helper for topic key
  private unsubscribeTopic(topic: string, cb: Listener) {
    const set = this.listeners.get(topic);
    if (!set) return;
    set.delete(cb);
    if (set.size === 0) {
      this.listeners.delete(topic);
      this.unsubscribeFromTopic(topic);
    }
  }

  unsubscribe(symbol: string, cb: Listener) {
    // backward-compat: remove any listener matching symbol across intervals
    const normalized = String(symbol).toUpperCase();
    for (const key of Array.from(this.listeners.keys())) {
      if (key.startsWith(normalized + ':')) {
        const set = this.listeners.get(key)!;
        set.delete(cb);
        if (set.size === 0) {
          this.listeners.delete(key);
          this.unsubscribeFromTopic(key);
        }
      }
    }
  }

  private handleMessage(raw: string, topic: string) {
    try {
      const obj = JSON.parse(raw);

      // Extract candle data from message
      let symbol = obj.symbol || obj.ticker || obj.s || obj.symbolName;
      if (!symbol && topic) {
        const parts = topic.split(':');
        if (parts.length > 0) symbol = parts[0];
      }
      const time = obj.openTime ? Math.floor(obj.openTime / 1000) : obj.timestamp ? Math.floor(obj.timestamp / 1000) : Math.floor(Date.now() / 1000);

      // try to extract volume from various possible fields
      const volRaw = obj.volume ?? obj.v ?? obj.q ?? obj.quoteVolume ?? obj.qty ?? obj.quote_qty ?? null;
      const vol = Number.isFinite(Number(volRaw)) ? Number(volRaw) : undefined;

      const candle: Candle = {
        time,
        open: Number(obj.open),
        high: Number(obj.high),
        low: Number(obj.low),
        close: Number(obj.close),
        symbol,
        ...(vol !== undefined ? { volume: vol } : {}),
      };

      if (this.debug) {
        console.debug('[sharedWs] incoming', { raw: obj, topic, candle });
      }

      // Dispatch to listeners for this topic
      const listeners = this.listeners.get(topic);
      if (listeners) {
        for (const cb of listeners) {
          try {
            cb(candle);
          } catch (e) {
            // listener errors shouldn't break dispatcher
          }
        }
      }
    } catch (e) {
      console.warn('[sharedWs] parse error', e);
    }
  }

  // Disconnect client (for cleanup)
  disconnect() {
    if (this.client) {
      this.client.deactivate();
    }
  }
}

export const sharedWs = new SharedWs();
