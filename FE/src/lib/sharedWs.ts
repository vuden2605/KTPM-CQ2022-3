type Candle = { time: number; open: number; high: number; low: number; close: number; symbol?: string };

type Listener = (c: Candle) => void;

const URL = 'ws://localhost:8083/ws';

class SharedWs {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<Listener>> = new Map();
  private subscribed: Set<string> = new Set();
  private reconnectAttempts = 0;
  private reconnectTimer: number | null = null;

  ensureConnected() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
    this.ws = new WebSocket(URL);
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      // re-subscribe to existing topics
      for (const s of this.subscribed) {
        this.sendSubscribe(s);
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

  private sendSubscribe(symbol: string) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    try {
      this.ws.send(JSON.stringify({ type: 'SUBSCRIBE', symbol, interval: '1m' }));
    } catch (e) {
      // ignore
    }
  }

  subscribe(symbol: string, cb: Listener) {
    const set = this.listeners.get(symbol) ?? new Set();
    set.add(cb);
    this.listeners.set(symbol, set);
    if (!this.subscribed.has(symbol)) {
      this.subscribed.add(symbol);
      this.ensureConnected();
      this.sendSubscribe(symbol);
    }
    return () => this.unsubscribe(symbol, cb);
  }

  unsubscribe(symbol: string, cb: Listener) {
    const set = this.listeners.get(symbol);
    if (!set) return;
    set.delete(cb);
    if (set.size === 0) {
      this.listeners.delete(symbol);
      this.subscribed.delete(symbol);
      // no unsubscribe message supported by backend; it's fine - server drops when session closed
    }
  }

  private handleMessage(raw: any) {
    try {
      let obj: any;
      if (typeof raw === 'string') obj = JSON.parse(raw);
      else obj = raw;
      // normalization: try to extract symbol and OHLC
      const symbol = obj.symbol || obj.ticker || obj.s || obj.symbolName;
      const time = obj.openTime ? Math.floor(obj.openTime / 1000) : obj.timestamp ? Math.floor(obj.timestamp / 1000) : Math.floor(Date.now() / 1000);
      const c = {
        time,
        open: Number(obj.open),
        high: Number(obj.high),
        low: Number(obj.low),
        close: Number(obj.close),
        symbol,
      } as Candle;
      if (symbol && this.listeners.has(symbol)) {
        for (const cb of this.listeners.get(symbol) || []) cb(c);
      } else {
        // if no symbol key, broadcast to all listeners
        for (const [, set] of this.listeners) {
          for (const cb of set) cb(c);
        }
      }
    } catch (e) {
      // ignore parse errors
      console.warn('sharedWs parse error', e);
    }
  }
}

export const sharedWs = new SharedWs();
