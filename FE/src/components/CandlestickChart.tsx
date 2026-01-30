import { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import type { CandlestickData, Time } from 'lightweight-charts';
import { sharedWs } from '../lib/sharedWs';

interface CandlestickChartProps {
  symbol: string;
  /** spacing for mock/historical candles in seconds (default 60) */
  intervalSeconds?: number;
  /** if true, do not subscribe to backend WS and use mock-only mode */
  useMockOnly?: boolean;
  onMetricsUpdate?: (metrics: { messagesPerSec: number; bufferSize: number; dropped: number; fps: number }) => void;
}

export const CandlestickChart = ({ symbol, intervalSeconds = 60, useMockOnly = false, onMetricsUpdate }: CandlestickChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const mockIntervalRef = useRef<number | null>(null);
  const incomingBufferRef = useRef<Array<CandlestickData & { symbol?: string }>>([]);
  const rafIdRef = useRef<number | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const [hover, setHover] = useState<{
    time?: number | null;
    open?: number | null;
    high?: number | null;
    low?: number | null;
    close?: number | null;
    vChange?: number | null; // value change (close - prevClose)
    vPercent?: number | null; // percent change vs prevClose
  }>({ time: null, open: null, high: null, low: null, close: null, vChange: null, vPercent: null });

  // Metrics refs
  const messagesInRef = useRef(0);
  const droppedRef = useRef(0);
  const frameCountRef = useRef(0);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: {
        background: { color: '#1e222d' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2b2f3a' },
        horzLines: { color: '#2b2f3a' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#2b2f3a',
        tickMarkFormatter: (time: number, tickMarkType: any, locale: string) => {
          const date = new Date(time * 1000);
          // Simple check: if hours/minutes are 0 and we are zooming out, we might want date. 
          // But 'tickMarkType' is reliable if imported. 
          // For now, simple logic:
          // If we are showing time (Type 0, 1):
          // Actually, let's just format to readable local string logic:
          // If it looks like midnight local, show date?
          // Let's stick to what user wanted: "Convert timezone" + "No seconds".
          // Only formatting time-level ticks. For Day level, it usually defaults to date string?
          // Actually, replacing tickMarkFormatter overrides EVERYTHING.

          // Heuristic:
          // TickMarkType: Year=0, Month=1, DayOfMonth=2, Time=3, TimeWithSeconds=4
          if (tickMarkType < 3) {
            return date.toLocaleDateString(locale);
          }
          return date.toLocaleTimeString(locale, {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          });
        },
      },
      rightPriceScale: {
        borderColor: '#2b2f3a',
      },
      localization: {
        // Use browser's local timezone
        timeFormatter: (timestamp: number) => {
          const date = new Date(timestamp * 1000);
          const d = date.getDate().toString().padStart(2, '0');
          const m = (date.getMonth() + 1).toString().padStart(2, '0');
          const y = date.getFullYear();
          const h = date.getHours().toString().padStart(2, '0');
          const min = date.getMinutes().toString().padStart(2, '0');
          return `${d}/${m}/${y} ${h}:${min}`;
        },
      },
    });

    const candlestickSeries = (chart as any).addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    // Add volume histogram series at the bottom
    const volumeSeries = (chart as any).addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '', // overlay on same pane
    });

    // Set volume series to bottom 20% of chart
    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8, // highest point at 80% from top
        bottom: 0,
      },
    });

    // Set candlestick to top 80% of chart
    candlestickSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.05,
        bottom: 0.25, // leave room for volume
      },
    });

    chartRef.current = chart;

    // subscribe to crosshair moves to show OHLCV(V, %) in a small overlay
    const onCrosshair = (param: any) => {
      try {
        if (!param || !param.time) {
          setHover({ time: null, open: null, high: null, low: null, close: null });
          return;
        }
        const seriesData = param.seriesData?.get(candlestickSeries as any);
        if (seriesData && typeof seriesData.open !== 'undefined') {
          const openN = Number(seriesData.open);
          const closeN = Number(seriesData.close);
          // find previous candle in seed (largest time < current)
          const curTime = (param.time as any).timestamp ?? param.time;
          let prevClose: number | null = null;
          for (let i = seed.length - 1; i >= 0; i--) {
            try {
              const t = Number((seed[i] as any).time);
              if (t < curTime) {
                prevClose = Number((seed[i] as any).close);
                break;
              }
            } catch (e) { /* ignore */ }
          }
          const vChange = prevClose !== null && Number.isFinite(prevClose) ? closeN - prevClose : 0;
          const vPercent = prevClose !== null && Number.isFinite(prevClose) && prevClose !== 0 ? (vChange / prevClose) * 100 : 0;
          setHover({
            time: curTime,
            open: openN,
            high: Number(seriesData.high),
            low: Number(seriesData.low),
            close: closeN,
            vChange,
            vPercent,
          });
        } else {
          setHover({ time: null, open: null, high: null, low: null, close: null, vChange: null, vPercent: null });
        }
      } catch (e) {
        // ignore
      }
    };
    const unsubCross = (chart as any).subscribeCrosshairMove(onCrosshair);

    // Handle resize - use ResizeObserver for container size changes (watchlist resize)
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    // Use ResizeObserver to detect container size changes (when watchlist is resized)
    const resizeObserver = new ResizeObserver(() => {
      handleResize();
    });
    if (chartContainerRef.current) {
      resizeObserver.observe(chartContainerRef.current);
    }

    // Compute backend interval and pageSize. Backend supports granular intervals
    // (1m,5m,15m,1h,4h,1d). For larger UI intervals (1W,1M,..) request multiple
    // `1d` candles instead of unsupported '7d' etc.
    const computeBackendRequest = (sec: number, limit = 1000) => {
      // direct mappings
      if (sec === 60) return { interval: '1m', pageSize: limit };
      if (sec === 300) return { interval: '5m', pageSize: limit };
      if (sec === 900) return { interval: '15m', pageSize: limit };
      if (sec === 3600) return { interval: '1h', pageSize: limit };
      if (sec === 14400) return { interval: '4h', pageSize: limit };
      if (sec === 86400) return { interval: '1d', pageSize: limit };

      // If it's a multiple of days, request daily candles and set pageSize to number of days
      if (sec % 86400 === 0) {
        const days = Math.min(Math.max(1, sec / 86400), limit);
        return { interval: '1d', pageSize: Math.min(limit, days) };
      }

      // Fallback to 1m
      return { interval: '1m', pageSize: limit };
    };

    // (Removed unused Binance direct fetch; using storage-service cached endpoint instead)

    window.addEventListener('resize', handleResize);


    // (mock candle generator removed — chart uses backend + realtime unless `useMockOnly` is enabled)

    // start with empty data; do NOT seed mock candles so UI only shows real backend/realtime data
    const seed: CandlestickData[] = [];
    const volumeSeed: { time: any; value: number; color: string }[] = [];
    candlestickSeries.setData(seed as any);
    volumeSeries.setData(volumeSeed as any);

    // Try to fetch cached recent candles from storage-service (Redis cache) and replace seed before subscribing
    // Buffer limits and helpers: used by history fetch and flush
    const MAX_STORE = 1000;
    // Max messages buffered before dropping oldest entries
    const MAX_BUFFER = 2000;

    // Helpers: sanitization/dedupe utilities used by history fetch and flush
    const makeAscendingUnique = (arr: CandlestickData[]) => {
      // Aggregate candles with same timestamp: keep first open, max high, min low, last close
      const map = new Map<number, CandlestickData>();
      for (const candle of arr) {
        const t = Number((candle as any).time);
        const existing = map.get(t);
        if (existing) {
          // Merge OHLC properly: first open, highest high, lowest low, latest close
          map.set(t, {
            time: t as Time,
            open: existing.open,  // keep first open
            high: Math.max(existing.high, candle.high),
            low: Math.min(existing.low, candle.low),
            close: candle.close,  // use latest close
          });
        } else {
          map.set(t, candle);
        }
      }
      const unique = Array.from(map.values());
      const sorted = unique.sort((a, b) => Number((a as any).time) - Number((b as any).time));
      return sorted;
    };

    const validateCandle = (c: CandlestickData) => {
      const o = Number((c as any).open);
      const h = Number((c as any).high);
      const l = Number((c as any).low);
      const cl = Number((c as any).close);
      if (![o, h, l, cl].every(Number.isFinite)) return false;
      if (![o, h, l, cl].every((x) => x > -1e6 && x < 1e9)) return false;
      if (h < l) return false;
      return true;
    };

    const sanitizeAndClamp = (arr: CandlestickData[]) => {
      const filtered = arr.filter((c) => validateCandle(c));
      // FILTER: only keep candles aligned to intervalSeconds (remove off-interval candles)
      const aligned = intervalSeconds > 1
        ? filtered.filter((c) => {
          const t = Number((c as any).time);
          return t % intervalSeconds === 0;
        })
        : filtered;
      // detect duplicates by time
      const freq = new Map<number, number>();
      for (const it of aligned) {
        const t = Number((it as any).time);
        freq.set(t, (freq.get(t) || 0) + 1);
      }
      const duplicates = aligned.filter((c) => (freq.get(Number((c as any).time)) || 0) > 1);
      const cleaned = makeAscendingUnique(aligned);
      if (cleaned.length > MAX_STORE) cleaned.splice(0, cleaned.length - MAX_STORE);
      const removedCount = arr.length - cleaned.length;
      const dupCount = duplicates.length;
      // only warn if significant removal occurred to avoid noisy logs
      if (removedCount > 5 || dupCount > 5) {
        console.info('sanitizeAndClamp removed/merged invalid or duplicate candles', {
          original: arr.length,
          kept: cleaned.length,
          removedCount,
          dupCount,
          removedSamples: arr
            .filter((x) => !aligned.includes(x))
            .slice(0, 6)
            .map((s) => ({ time: (s as any).time, open: (s as any).open, high: (s as any).high, low: (s as any).low, close: (s as any).close })),
          duplicateSamples: duplicates.slice(0, 6).map((s) => ({ time: (s as any).time, open: (s as any).open, high: (s as any).high, low: (s as any).low, close: (s as any).close })),
        });
      }
      return cleaned;
    };

    const fetchCachedRecent = async (sym: string, intervalSec: number, limit = 1000) => {
      try {
        // storage-service runs on 8082
        const backend = computeBackendRequest(intervalSec, limit);
        const interval = backend.interval;
        const pageSize = backend.pageSize ?? limit;
        const API_BASE = (import.meta.env.VITE_API_BASE as string) || 'http://localhost:80';
        const url = `${API_BASE}/api/v1/candles/recent?symbol=${encodeURIComponent(sym)}&interval=${interval}&pageSize=${pageSize}`;
        const token = localStorage.getItem('accessToken');
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const resp = await fetch(url, { headers });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const api = await resp.json();
        // ApiResponse.data is List<CandleCreationRequest> where time is in ms
        if (!api || !api.data) return null;
        const data: any[] = api.data;
        // Keep only one candle per unique timestamp (last occurrence for any realtime updates)
        const uniqueMap = new Map<number, any>();
        for (const c of data) {
          // tolerate various backend time units (ms, s). Accept fields like openTime.
          const raw = Number(c.openTime ?? c.open_time ?? c.time ?? 0);
          if (!Number.isFinite(raw)) continue;
          let baseTime = Math.floor(raw);
          // if value looks like milliseconds (>= year 2001 in ms ~ 1000_000_000_000), convert to seconds
          if (raw > 1e12) baseTime = Math.floor(raw / 1000);
          // some backends may send microseconds/nanoseconds; coerce large numbers down
          if (raw > 1e15) baseTime = Math.floor(raw / 1000000);
          const nowSec = Math.floor(Date.now() / 1000);
          // guard: ignore obviously wrong timestamps (before 2000 or far future)
          if (baseTime < 946684800 || baseTime > nowSec + 86400) {
            console.warn('Suspicious openTime from backend, skipping', { raw, baseTime, symbol });
            continue;
          }
          uniqueMap.set(baseTime, c);
        }

        const candles: CandlestickData[] = [];
        for (const [baseTime, c] of uniqueMap.entries()) {
          // bucket historical timestamps to requested interval to ensure alignment
          const bucket = intervalSec && intervalSec > 1 ? Math.floor(baseTime / intervalSec) * intervalSec : baseTime;
          // try to include volume if backend provided it under common keys
          const volRaw = c.volume ?? c.vol ?? c.v ?? c.quoteVolume ?? c.quote_vol ?? c.qty ?? c.q ?? null;
          const vol = Number.isFinite(Number(volRaw)) ? Number(volRaw) : undefined;
          candles.push({
            time: bucket as Time,
            open: +c.open,
            high: +c.high,
            low: +c.low,
            close: +c.close,
            ...(vol !== undefined ? { volume: vol } : {}),
          } as any);
        }

        // Sort by time to ensure correct order
        candles.sort((a, b) => Number((a as any).time) - Number((b as any).time));
        return candles;
      } catch (e) {
        console.warn('Cached recent fetch failed', e);
        return null;
      }
    };

    // Try to fetch cached recent candles and replace seed before subscribing (actual fetch happens after subscription helper is defined)

    // Flush buffer to chart to batch updates
    let isUnmounted = false;
    // symbol for this chart instance (captured by this effect)
    const expectedSymbol = symbol.toUpperCase();

    const flush = () => {
      if (isUnmounted) return;
      const rawItems = incomingBufferRef.current.splice(0);
      // Only process items that match the expected symbol for this chart instance
      const items = rawItems.filter((it) => {
        try {
          const s = (it as any).symbol;
          if (!s) return false;
          return String(s).toUpperCase() === expectedSymbol;
        } catch (e) {
          return false;
        }
      });
      // count dropped cross-symbol items
      const droppedCount = rawItems.length - items.length;
      if (droppedCount > 0) droppedRef.current += droppedCount;
      frameCountRef.current++;
      if (items.length === 0) {
        rafIdRef.current = requestAnimationFrame(flush);
        return;
      }

      // Keep times as-is since they already have unique millisecond offsets
      const normalizeTime = (d: CandlestickData) => ({ ...d, time: Number((d as any).time) as Time });
      const normalized = items.map(normalizeTime);

      const lastSeedTime = seed.length ? Number((seed[seed.length - 1] as any).time) : -Infinity;

      // treat strictly older items as "older"; equal-time items are treated as updates
      const hasOlder = normalized.some((it) => Number((it as any).time) < lastSeedTime);

      if (hasOlder || normalized.length > 0) {
        // Append all new candles without merging, just sort
        seed.push(...normalized);
        let out = sanitizeAndClamp(seed);
        seed.length = 0;
        seed.push(...out);
        try {
          candlestickSeries.setData(seed as any);
          // Update volume histogram with colors matching candle direction
          const volumeData = seed.map((c: any) => ({
            time: c.time,
            value: c.volume || 0,
            color: c.close >= c.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
          }));
          volumeSeries.setData(volumeData);
        } catch (e) {
          console.warn('setData failed, retrying sanitized', e);
          candlestickSeries.setData(sanitizeAndClamp(seed) as any);
        }
      }

      rafIdRef.current = requestAnimationFrame(flush);
    };

    rafIdRef.current = requestAnimationFrame(flush);

    // If websocket never opens, start mock updates
    const startMockUpdates = () => {
      if (mockIntervalRef.current) return;
      mockIntervalRef.current = window.setInterval(() => {
        try {
          // create a new candle based on last known
          const lastIndex = seed.length ? seed[seed.length - 1] : undefined;
          const lastClose = lastIndex ? lastIndex.close : 56900;
          const open = +(lastClose + (Math.random() - 0.5) * 200).toFixed(2);
          const high = +(Math.max(open, lastClose) + Math.random() * 100).toFixed(2);
          const low = +(Math.min(open, lastClose) - Math.random() * 100).toFixed(2);
          const close = +(low + Math.random() * (high - low)).toFixed(2);
          const candleData: CandlestickData = {
            time: Math.floor(Date.now() / 1000) as Time,
            open,
            high,
            low,
            close,
          };
          if (!isUnmounted) {
            candlestickSeries.update(candleData as any);
            seed.push(candleData);
          }
        } catch (e) {
          console.error('mock update error', e);
        }
      }, 1500);
    };


    // Subscribe to shared WebSocket and receive normalized candle data (unless mock-only)
    let unsubscribe: (() => void) | null = null;
    const setupSubscription = () => {
      if (useMockOnly) return;
      // clear any leftover buffered messages when switching symbols
      incomingBufferRef.current.length = 0;
      droppedRef.current = 0;
      messagesInRef.current = 0;
      frameCountRef.current = 0;

      // use expectedSymbol declared in outer scope
      // Subscribe to the backend interval that best matches the selected UI interval
      // (backend may support 1m/5m/15m/1h/4h/1d). We compute the backend interval
      // from `intervalSeconds` so subscriptions are made per symbol+interval.
      const backendReq = computeBackendRequest(intervalSeconds, 1);
      const intervalStr = backendReq.interval;
      // subscribe log removed (debug)
      unsubscribe = sharedWs.subscribe(symbol, (candle) => {
        // Strictly require the payload to include a symbol and match expectedSymbol.
        if (!candle || !(candle as any).symbol) {
          return;
        }
        try {
          if (String((candle as any).symbol).toUpperCase() !== expectedSymbol) {
            return;
          }
        } catch (e) {
          return;
        }
        // otherwise proceed
        // push normalized data into buffer with drop-old policy
        if (incomingBufferRef.current.length >= MAX_BUFFER) {
          incomingBufferRef.current.shift();
          droppedRef.current++;
        }
        const rawT = Math.floor(Number((candle as any).time));
        // bucket incoming times to the selected interval to ensure aggregation
        // (handles cases where backend may send higher-frequency ticks)
        const bucket = intervalSeconds && intervalSeconds > 1 ? Math.floor(rawT / intervalSeconds) * intervalSeconds : rawT;
        const cd: CandlestickData & { symbol?: string } = {
          time: bucket as Time,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
          symbol: (candle as any).symbol ?? expectedSymbol,
        };
        // Append incoming candle (dedupe happens in flush via sanitizeAndClamp)
        incomingBufferRef.current.push(cd);
        messagesInRef.current++;
      }, intervalStr);

      // Ensure shared WS connection is active (subscribe to backend-supported interval)
      sharedWs.ensureConnected();
    };
    // start mock updates if requested; otherwise fetch history then setup subscription
    if (useMockOnly) {
      startMockUpdates();
    } else {
      (async () => {
        try {
          const history = await fetchCachedRecent(symbol, intervalSeconds, 1000);
          if (history && history.length) {
            const sanitized = sanitizeAndClamp(history);
            seed.length = 0;
            seed.push(...sanitized);
            try {
              candlestickSeries.setData(seed as any);
            } catch (e) {
              console.error('setData failed for fetched history; dumping times', e, {
                times: (seed as any).map((s: any) => ({ time: s.time, type: typeof s.time })),
              });
              candlestickSeries.setData(sanitizeAndClamp(seed) as any);
            }
          }
        } catch (e) {
          console.warn('history fetch failed before subscribe', e);
        }
        setupSubscription();
      })();
    }

    // Metrics update intervals
    const metricsInterval = setInterval(() => {
      const msgs = messagesInRef.current;
      messagesInRef.current = 0;

      const buf = incomingBufferRef.current.length;
      const drp = droppedRef.current;
      const fps = frameCountRef.current;
      frameCountRef.current = 0;

      if (onMetricsUpdate) {
        onMetricsUpdate({
          messagesPerSec: msgs,
          bufferSize: buf,
          dropped: drp,
          fps: fps
        });
      }
    }, 1000);

    return () => {
      // mark unmounted so flush/mock won't run
      isUnmounted = true;
      // clear any pending buffer and metrics so next mount starts clean
      try { incomingBufferRef.current.length = 0; } catch (e) { }
      try { droppedRef.current = 0; } catch (e) { }
      try { messagesInRef.current = 0; } catch (e) { }
      try { frameCountRef.current = 0; } catch (e) { }
      // Cleanup resize observer
      resizeObserver.disconnect();
      window.removeEventListener('resize', handleResize);
      // unsubscribe from shared ws
      try {
        if (unsubscribe) {
          unsubscribe();
        }
      } catch (e) { }

      // stop reconnect timers
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      // stop intervals and RAF before removing the chart to avoid "Object is disposed"
      if (mockIntervalRef.current) {
        clearInterval(mockIntervalRef.current as number);
        mockIntervalRef.current = null;
      }
      try { if (unsubCross) unsubCross(); } catch (e) { }
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      clearInterval(metricsInterval);

      // finally remove chart instance
      try { chart.remove(); } catch (e) { }
    };
  }, [symbol, intervalSeconds, useMockOnly]);

  return (
    <div
      ref={chartContainerRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'relative'
      }}
    >
      {/* Hover OHLCV overlay */}
      <div style={{ position: 'absolute', left: 16, top: 10, zIndex: 40, pointerEvents: 'none', maxWidth: 'calc(100% - 100px)' }}>
        <div style={{
          color: '#d1d4dc',
          fontSize: 12,
          display: 'flex',
          gap: 12, /* Reduced gap to fit more */
          flexWrap: 'wrap', /* Allow wrapping */
          fontFamily: 'JetBrains Mono, monospace'
        }}>
          <span style={{ fontWeight: 600, color: '#d1d4dc' }}>{symbol.toUpperCase()}</span>

          {hover && hover.time ? (
            <>
              <span style={{ color: '#d1d4dc', marginRight: 8 }}>
                {(() => {
                  const date = new Date((hover.time || 0) * 1000);
                  const d = date.getDate().toString().padStart(2, '0');
                  const m = (date.getMonth() + 1).toString().padStart(2, '0');
                  const y = date.getFullYear();
                  const h = date.getHours().toString().padStart(2, '0');
                  const min = date.getMinutes().toString().padStart(2, '0');
                  return `${d}/${m}/${y} ${h}:${min}`;
                })()}
              </span>
              <span style={{ color: '#787b86' }}>
                O <span className={(hover.open ?? 0) <= (hover.close ?? 0) ? 'text-up' : 'text-down'}>{typeof hover.open === 'number' ? hover.open.toFixed(4) : '-'}</span>
              </span>
              <span style={{ color: '#787b86' }}>
                H <span className={(hover.open ?? 0) <= (hover.close ?? 0) ? 'text-up' : 'text-down'}>{typeof hover.high === 'number' ? hover.high.toFixed(4) : '-'}</span>
              </span>
              <span style={{ color: '#787b86' }}>
                L <span className={(hover.open ?? 0) <= (hover.close ?? 0) ? 'text-up' : 'text-down'}>{typeof hover.low === 'number' ? hover.low.toFixed(4) : '-'}</span>
              </span>
              <span style={{ color: '#787b86' }}>
                C <span className={(hover.open ?? 0) <= (hover.close ?? 0) ? 'text-up' : 'text-down'}>{typeof hover.close === 'number' ? hover.close.toFixed(4) : '-'}</span>
              </span>
              <span style={{ color: '#787b86' }}>
                Vol <span className={(hover as any).vChange >= 0 ? 'text-up' : 'text-down'}>{typeof (hover as any).vChange === 'number' ? ((hover as any).vChange >= 0 ? '+' : '') + (hover as any).vChange.toFixed(2) : '-'} ({typeof (hover as any).vPercent === 'number' ? ((hover as any).vPercent >= 0 ? '+' : '') + (hover as any).vPercent.toFixed(2) + '%' : ''})</span>
              </span>
            </>
          ) : (
            <span style={{ color: '#787b86' }}>Moving cursor to see data</span>
          )}
        </div>

        <style>{`
            .text-up { color: #26a69a; }
            .text-down { color: #ef5350; }
          `}</style>
      </div>
    </div>
  );
};
