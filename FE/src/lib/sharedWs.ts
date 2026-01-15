type Candle = { time: number; open: number; high: number; low: number; close: number; symbol?: string };

type Listener = (c: Candle) => void;

const URL = 'ws://localhost:8083/ws';

class SharedWs {
  private ws: WebSocket | null = null;
  // listeners keyed by "SYMBOL:INTERVAL" (e.g. "BTCUSDT:1m")
  private listeners: Map<string, Set<Listener>> = new Map();
  // track subscribed topics sent to backend (same key format)
  private subscribed: Set<string> = new Set();
  private reconnectAttempts = 0;
  private reconnectTimer: number | null = null;

  ensureConnected() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
    this.ws = new WebSocket(URL);
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      // re-subscribe to existing topics
      for (const topic of this.subscribed) {
        // topic stored as SYMBOL:INTERVAL
        const parts = topic.split(':');
        const symbol = parts[0];
        const interval = parts[1] || '1m';
        this.sendSubscribe(symbol, interval);
      }
    };
    this.ws.onmessage = (ev) => this.handleMessage(ev.data);
    this.ws.onclose = () => this.scheduleReconnect();
    this.ws.onerror = () => this.scheduleReconnect();
  }

  private scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    if (this.reconnectTimer) window.clearTimeout(this.reconnectTimer);
    this.reconnectTimer = window.setTimeout(() => {
      this.ensureConnected();
    }, delay);
  }

  private sendSubscribe(symbol: string, interval: string = '1m') {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    try {
      this.ws.send(JSON.stringify({ type: 'SUBSCRIBE', symbol, interval }));
    } catch (e) {
      // ignore
    }
  }

  subscribe(symbol: string, cb: Listener, interval: string = '1m') {
    const normalized = String(symbol).toUpperCase();
    const topic = `${normalized}:${interval}`;
    const set = this.listeners.get(topic) ?? new Set();
    set.add(cb);
    this.listeners.set(topic, set);
    if (!this.subscribed.has(topic)) {
      this.subscribed.add(topic);
      this.ensureConnected();
      this.sendSubscribe(normalized, interval);
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
      this.subscribed.delete(topic);
      // no unsubscribe message supported by backend; it's fine - server drops when session closed
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
          this.subscribed.delete(key);
        }
      }
    }
  }

  private handleMessage(raw: any) {
    try {
      let obj: any;
      if (typeof raw === 'string') obj = JSON.parse(raw);
      else obj = raw;
      // normalization: try to extract symbol and OHLC
      const symbol = obj.symbol || obj.ticker || obj.s || obj.symbolName;
      const interval = obj.interval || obj.i || obj.k?.interval || null;
      const time = obj.openTime ? Math.floor(obj.openTime / 1000) : obj.timestamp ? Math.floor(obj.timestamp / 1000) : Math.floor(Date.now() / 1000);
      const c = {
        time,
        open: Number(obj.open),
        high: Number(obj.high),
        low: Number(obj.low),
        close: Number(obj.close),
        symbol,
        // include interval if present so listeners can inspect
        ...(interval ? { interval } : {}),
      } as Candle;

      if (symbol && interval) {
        const topic = `${String(symbol).toUpperCase()}:${interval}`;
        if (this.listeners.has(topic)) {
          for (const cb of this.listeners.get(topic) || []) cb(c);
        }
        // DO NOT fallback broadcast: only dispatch to exact interval match
        // This prevents 1m data from being sent to 5m/15m/etc listeners
        return;
      }

      // If no interval in message, log warning and ignore (backend should always include interval)
      if (symbol) {
        console.warn('Received WS message without interval field, ignoring', { symbol, obj });
        return;
      }

      // No symbol or interval: ignore
      console.warn('Received WS message without symbol/interval, ignoring', obj);
    } catch (e) {
      // ignore parse errors
      console.warn('sharedWs parse error', e);
    }
  }
}

export const sharedWs = new SharedWs();
