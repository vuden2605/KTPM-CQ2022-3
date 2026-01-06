import { decode } from '@msgpack/msgpack';

type Raw = string | ArrayBuffer | Uint8Array;

function parseRaw(raw: Raw) {
  // Try MessagePack first (ArrayBuffer or Uint8Array)
  if (raw instanceof ArrayBuffer || raw instanceof Uint8Array) {
    try {
      const buf = raw instanceof Uint8Array ? raw : new Uint8Array(raw);
      const obj = decode(buf) as any;
      return obj;
    } catch (e) {
      // fallthrough to try text parse
    }
  }

  // If it's a string, parse JSON
  if (typeof raw === 'string') {
    try {
      return JSON.parse(raw);
    } catch (e) {
      return null;
    }
  }

  return null;
}

function normalizeCandle(obj: any) {
  if (!obj) return null;

  // If obj is an array [t,o,h,l,c]
  if (Array.isArray(obj)) {
    const [t, o, h, l, c] = obj;
    const time = typeof t === 'number' ? Math.floor(t / (t > 1e12 ? 1000 : 1)) : Math.floor(Date.now() / 1000);
    return {
      time,
      open: Number(o),
      high: Number(h),
      low: Number(l),
      close: Number(c),
    };
  }

  // If object contains 'k' (Binance), extract k
  if (obj.k) obj = obj.k;

  // Common fields: openTime / open, or timestamp
  const openTime = obj.openTime || obj.open_time || obj.t || obj.openTs || null;
  const timestamp = obj.timestamp || obj.time || obj.T || null;

  let timeSec = Math.floor(Date.now() / 1000);
  if (openTime) {
    const t = typeof openTime === 'string' ? Date.parse(openTime) : Number(openTime);
    timeSec = Math.floor((t && t > 0 ? t : Date.now()) / 1000);
  } else if (timestamp) {
    const t = Number(timestamp);
    timeSec = Math.floor((t > 1e12 ? t / 1000 : t) || Date.now() / 1000);
  }

  const o = obj.open ?? obj.o ?? obj.Open ?? obj.openPrice;
  const h = obj.high ?? obj.h ?? obj.High ?? obj.highPrice;
  const l = obj.low ?? obj.l ?? obj.Low ?? obj.lowPrice;
  const c = obj.close ?? obj.c ?? obj.Close ?? obj.closePrice;

  return {
    time: timeSec,
    open: Number(o),
    high: Number(h),
    low: Number(l),
    close: Number(c),
  };
}

self.addEventListener('message', (e) => {
  const raw = e.data;
  const obj = parseRaw(raw);
  const normalized = normalizeCandle(obj);
  if (normalized) {
    // post normalized candle
    // use postMessage with transfer for objects not needed
    (self as any).postMessage(normalized);
  }
});
