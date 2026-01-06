import { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import type { CandlestickData, Time } from 'lightweight-charts';
import { MetricsPanel } from './MetricsPanel';
import { sharedWs } from '../lib/sharedWs';

interface CandlestickChartProps {
  symbol: string;
  /** spacing for mock/historical candles in seconds (default 60) */
  intervalSeconds?: number;
  /** if true, do not subscribe to backend WS and use mock-only mode */
  useMockOnly?: boolean;
}

export const CandlestickChart = ({ symbol, intervalSeconds = 60, useMockOnly = false }: CandlestickChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const mockIntervalRef = useRef<number | null>(null);
  const websocketOpenedRef = useRef(false);
  const incomingBufferRef = useRef<CandlestickData[]>([]);
  const rafIdRef = useRef<number | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  // Metrics state
  const [messagesPerSec, setMessagesPerSec] = useState(0);
  const [bufferSize, setBufferSize] = useState(0);
  const [dropped, setDropped] = useState(0);
  const [fps, setFps] = useState(0);

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
      },
      rightPriceScale: {
        borderColor: '#2b2f3a',
      },
    });

    const candlestickSeries = (chart as any).addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    chartRef.current = chart;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    // Convert seconds to Binance interval string (best-effort)
    const secondsToBinanceInterval = (sec: number) => {
      switch (sec) {
        case 60:
          return '1m';
        case 300:
          return '5m';
        case 900:
          return '15m';
        case 3600:
          return '1h';
        case 14400:
          return '4h';
        case 86400:
          return '1d';
        default:
          // fallback: choose nearest common interval
          if (sec % 86400 === 0) return `${sec / 86400}d`;
          if (sec % 3600 === 0) return `${sec / 3600}h`;
          if (sec % 60 === 0) return `${sec / 60}m`;
          return '1m';
      }
    };

    // Fetch recent candles directly from Binance REST to seed chart immediately
    const fetchBinanceHistory = async (sym: string, intervalSec: number, limit = 500) => {
      try {
        const interval = secondsToBinanceInterval(intervalSec);
        // Use local ws-service proxy to avoid CORS issues
        const url = `http://localhost:8083/proxy/klines?symbol=${encodeURIComponent(sym)}&interval=${interval}&limit=${limit}`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data: any[] = await resp.json();
        // Each item: [ openTime, open, high, low, close, ... ]
        const candles: CandlestickData[] = data.map((k) => ({
          time: Math.floor(k[0] / 1000) as Time,
          open: +k[1],
          high: +k[2],
          low: +k[3],
          close: +k[4],
        }));
        return candles;
      } catch (e) {
        console.warn('Binance history fetch failed', e);
        return null;
      }
    };

    window.addEventListener('resize', handleResize);

    // Helper: generate mock historical candles
    const generateMockCandles = (count: number, base = 1000, intervalSec = intervalSeconds) => {
      // generate candles spaced by `intervalSeconds` to match the WS interval (default 1m)
      const now = Math.floor(Date.now() / 1000);
      const candles: CandlestickData[] = [];
      let lastClose = base;
      for (let i = count - 1; i >= 0; i--) {
        const time = now - i * intervalSec; // spaced by intervalSec (seconds)
        const open = +(lastClose + (Math.random() - 0.5) * base * 0.02).toFixed(2);
        const high = +(Math.max(open, lastClose) + Math.random() * base * 0.01).toFixed(2);
        const low = +(Math.min(open, lastClose) - Math.random() * base * 0.01).toFixed(2);
        const close = +(low + Math.random() * (high - low)).toFixed(2);
        candles.push({ time: time as Time, open, high, low, close });
        lastClose = close;
      }
      return candles;
    };

    // seed with mock data so chart shows something immediately (will be replaced by real history if available)
    const seed = generateMockCandles(80, 56900, intervalSeconds); // seed spacing matches `intervalSeconds`
    candlestickSeries.setData(seed as any);

    // Try to fetch real historical candles from Binance and replace seed before subscribing
    if (!useMockOnly) {
      (async () => {
        const history = await fetchBinanceHistory(symbol, intervalSeconds, 500);
        if (history && history.length) {
          // replace seed contents and update chart
          seed.length = 0;
          seed.push(...history);
          candlestickSeries.setData(seed as any);
        }
      })();
    }

    // Flush buffer to chart to batch updates
    const MAX_STORE = 500;
    // Max messages buffered before dropping oldest entries
    const MAX_BUFFER = 2000;
    let isUnmounted = false;

    const flush = () => {
      if (isUnmounted) return;
      const items = incomingBufferRef.current.splice(0);
      frameCountRef.current++;
      if (items.length === 0) {
        rafIdRef.current = requestAnimationFrame(flush);
        return;
      }

      // coerce times to numbers and ensure ordering
      const normalizeTime = (d: CandlestickData) => ({ ...d, time: Number((d as any).time) as Time });
      const normalized = items.map(normalizeTime);

      const lastSeedTime = seed.length ? Number((seed[seed.length - 1] as any).time) : -Infinity;

      const hasOlder = normalized.some((it) => Number((it as any).time) <= lastSeedTime);

      if (hasOlder) {
        // merge, dedupe by time, sort, and setData once
        const merged = [...seed, ...normalized];
        const map = new Map<number, CandlestickData>();
        for (const it of merged) {
          map.set(Number((it as any).time), it);
        }
        const sorted = Array.from(map.entries()).sort((a, b) => a[0] - b[0]).map(([, v]) => v);
        // clamp store size
        if (sorted.length > MAX_STORE) sorted.splice(0, sorted.length - MAX_STORE);
        seed.length = 0;
        seed.push(...sorted);
        candlestickSeries.setData(seed as any);
      } else if (normalized.length === 1) {
        // single incoming candle -> update
        candlestickSeries.update(normalized[0] as any);
        seed.push(normalized[0]);
      } else {
        // multiple items -> append and setData once
        seed.push(...normalized);
        if (seed.length > MAX_STORE) seed.splice(0, seed.length - MAX_STORE);
        candlestickSeries.setData(seed as any);
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
      unsubscribe = sharedWs.subscribe(symbol, (candle) => {
        // push normalized data into buffer with drop-old policy
        if (incomingBufferRef.current.length >= MAX_BUFFER) {
          incomingBufferRef.current.shift();
          droppedRef.current++;
        }
        const cd: CandlestickData = {
          time: Math.floor(candle.time) as Time,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
        };
        incomingBufferRef.current.push(cd);
        messagesInRef.current++;
      });

      // Ensure shared WS connection is active
      sharedWs.ensureConnected();
    };
    // start mock updates if requested; otherwise setup subscription now
    if (useMockOnly) startMockUpdates();
    else setupSubscription();

    // Fallback: if websocket not opened in 700ms, start mock updates
    setTimeout(() => {
      if (!websocketOpenedRef.current) startMockUpdates();
    }, 700);

    // no need to keep websocket in state for now

    // Metrics update intervals
    const msgInterval = setInterval(() => {
      setMessagesPerSec(messagesInRef.current);
      messagesInRef.current = 0;
    }, 1000);

    const metricsInterval = setInterval(() => {
      setBufferSize(incomingBufferRef.current.length);
      setDropped(droppedRef.current);
      setFps(frameCountRef.current);
      frameCountRef.current = 0;
    }, 1000);

    return () => {
      // mark unmounted so flush/mock won't run
      isUnmounted = true;
      window.removeEventListener('resize', handleResize);
      // unsubscribe from shared ws
      try { if (unsubscribe) unsubscribe(); } catch (e) { }

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
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      clearInterval(msgInterval);
      clearInterval(metricsInterval);

      // finally remove chart instance
      try { chart.remove(); } catch (e) { }
    };
  }, [symbol]);

  return (
    <div
      ref={chartContainerRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'relative'
      }}
    >
      <MetricsPanel messagesPerSec={messagesPerSec} bufferSize={bufferSize} dropped={dropped} fps={fps} />
    </div>
  );
};
