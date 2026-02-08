import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createChart } from 'lightweight-charts';
import type { CandlestickData, Time, SeriesMarker } from 'lightweight-charts';
import { sharedWs } from '../lib/sharedWs';
import { calculateSMA, calculateEMA } from '../lib/indicators';

interface CandlestickChartProps {
  symbol: string;
  /** spacing for mock/historical candles in seconds (default 60) */
  intervalSeconds?: number;
  /** if true, do not subscribe to backend WS and use mock-only mode */
  useMockOnly?: boolean;
  onMetricsUpdate?: (metrics: { messagesPerSec: number; bufferSize: number; dropped: number; fps: number }) => void;
  showSMA?: boolean;
  showEMA?: boolean;
  showNews?: boolean;
}

export const CandlestickChart = ({
  symbol,
  intervalSeconds = 60,
  useMockOnly = false,
  onMetricsUpdate,
  showSMA = true,
  showEMA = true,
  showNews = true
}: CandlestickChartProps) => {
  const navigate = useNavigate();
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const mockIntervalRef = useRef<number | null>(null);
  const incomingBufferRef = useRef<Array<CandlestickData & { symbol?: string }>>([]);

  const rafIdRef = useRef<number | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const candlestickSeriesRef = useRef<any>(null);
  const smaSeriesRef = useRef<any>(null);
  const emaSeriesRef = useRef<any>(null);
  const showNewsRef = useRef(showNews); // Track current showNews value

  const [hover, setHover] = useState<{
    time?: number | null;
    open?: number | null;
    high?: number | null;
    low?: number | null;
    close?: number | null;
    vChange?: number | null; // value change (close - prevClose)
    vPercent?: number | null; // percent change vs prevClose
    sma?: number | null;
    ema?: number | null;
    hasNews?: boolean | null;
  }>({ time: null, open: null, high: null, low: null, close: null, vChange: null, vPercent: null, sma: null, ema: null, hasNews: null });

  // News Widget State
  const [showNewsPopover, setShowNewsPopover] = useState(false);
  const [newsList, setNewsList] = useState<any[]>([]);

  // Interval News Popover State (clicked marker)
  const [intervalNews, setIntervalNews] = useState<{
    visible: boolean;
    items: any[];
    x: number;
    y: number;
    rangeLabel: string;
  }>({ visible: false, items: [], x: 0, y: 0, rangeLabel: '' });

  // Click outside to close popover
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        showNewsPopover &&
        buttonContainerRef.current &&
        !buttonContainerRef.current.contains(event.target as Node)
      ) {
        setShowNewsPopover(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showNewsPopover]);

  // Ref for the latest candle time to anchor the button
  const latestTimeRef = useRef<Time | null>(null);
  const buttonContainerRef = useRef<HTMLDivElement>(null);
  const newsMapRef = useRef<Map<number, any[]>>(new Map()); // Time (seconds) -> News Items
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


    // Assign to ref for access in other effects
    candlestickSeriesRef.current = candlestickSeries;

    // --- INDICATORS ---
    // SMA (20) - Yellow
    const smaSeries = (chart as any).addLineSeries({
      color: '#f1c40f',
      lineWidth: 2,
      crosshairMarkerVisible: false,
      visible: showSMA,
    });
    smaSeriesRef.current = smaSeries;

    // EMA (50) - Blue
    const emaSeries = (chart as any).addLineSeries({
      color: '#3498db',
      lineWidth: 2,
      crosshairMarkerVisible: false,
      visible: showEMA,
    });
    emaSeriesRef.current = emaSeries;
    // ------------------

    chartRef.current = chart;

    // Helper to update button position
    const updateButtonPosition = () => {
      if (!buttonContainerRef.current || !chartRef.current || !latestTimeRef.current || !chartContainerRef.current) return;

      const chart = chartRef.current;
      const x = (chart as any).timeScale().timeToCoordinate(latestTimeRef.current);

      if (x === null) {
        // Off screen or invalid (null)
        buttonContainerRef.current.style.display = 'none';
        return;
      }

      // Ensure button doesn't overlap the right Price Scale (Y-axis)
      const containerWidth = chartContainerRef.current.clientWidth;
      const safeX = Math.min(x, containerWidth - 80); // 80px buffer to clear axis

      // Show and position
      buttonContainerRef.current.style.display = 'flex';
      buttonContainerRef.current.style.left = `${safeX}px`;
      // Adjust transform to center the button (width 24px -> -12px)
      buttonContainerRef.current.style.transform = 'translateX(-50%)';
    };

    // Subscribe to time scale changes (scrolling/panning)
    (chart as any).timeScale().subscribeVisibleTimeRangeChange(() => {
      updateButtonPosition();
    });

    // subscribe to crosshair moves to show OHLCV(V, %) in a small overlay
    const onCrosshair = (param: any) => {
      try {
        if (!param || !param.time) {
          setHover({ time: null, open: null, high: null, low: null, close: null, vChange: null, vPercent: null, sma: null, ema: null, hasNews: null });
          document.body.style.cursor = 'default';
          return;
        }
        const seriesData = param.seriesData?.get(candlestickSeries as any);
        const smaVal = param.seriesData?.get(smaSeries as any)?.value;
        const emaVal = param.seriesData?.get(emaSeries as any)?.value;

        // Check for news
        const t = (param.time as any).timestamp ?? param.time;
        // Only consider news if feature is enabled (use ref to get latest value)
        const hasNews = showNewsRef.current && newsMapRef.current?.has(Number(t));

        // Change cursor if news exists
        if (chartContainerRef.current) {
          chartContainerRef.current.style.cursor = hasNews ? 'pointer' : 'crosshair';
        }

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
            sma: smaVal,
            ema: emaVal,
            hasNews,
          });
        } else {
          setHover({ time: null, open: null, high: null, low: null, close: null, vChange: null, vPercent: null, sma: smaVal, ema: emaVal, hasNews });
        }
      } catch (e) {
        // ignore
      }
    };
    const unsubCross = (chart as any).subscribeCrosshairMove(onCrosshair);

    // Handle Clicks
    const onClick = (param: any) => {
      if (!param || !param.time || !newsMapRef.current || !showNewsRef.current) return;

      const t = (param.time as any).timestamp ?? param.time;
      const tNum = Number(t);

      // Check if this time has news items
      const items = newsMapRef.current.get(tNum);

      if (items && items.length > 0) {
        // Calculate range label
        const startDate = new Date(tNum * 1000);
        const endDate = new Date((tNum + intervalSeconds) * 1000);

        const formatTime = (d: Date) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        // e.g. "14:00 - 15:00" or date if interval is large
        const rangeLabel = `${startDate.toLocaleDateString()} ${formatTime(startDate)} - ${formatTime(endDate)}`;

        // Get click coordinates for positioning (optional, or center it)
        // We'll just center it or use a fixed position like a modal
        setIntervalNews({
          visible: true,
          items: items,
          x: param.point?.x ?? 0,
          y: param.point?.y ?? 0,
          rangeLabel
        });
      }
    };
    (chart as any).subscribeClick(onClick);

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
    const makeAscendingUnique = (arr: CandlestickData[], simulateVolume = false) => {
      // Aggregate candles with same timestamp: keep first open, max high, min low, last close
      const map = new Map<number, CandlestickData>();
      for (const candle of arr) {
        const t = Number((candle as any).time);
        const existing = map.get(t);
        if (existing) {
          // Merge OHLC properly: first open, highest high, lowest low, latest close
          const newVol = (candle as any).volume;
          const prevVol = (existing as any).volume || 0;
          let finalVol = newVol;

          if (newVol === undefined) {
            // If incoming has no volume, either use previous or accumulate if simulating
            if (simulateVolume) {
              // Simulate tick volume: smaller random increment to avoid huge spikes
              finalVol = prevVol + (Math.random() * 0.2 + 0.1);
            } else {
              finalVol = prevVol;
            }
          }

          map.set(t, {
            time: t as Time,
            open: existing.open,  // keep first open
            high: Math.max(existing.high, candle.high),
            low: Math.min(existing.low, candle.low),
            close: candle.close,  // use latest close
            volume: finalVol,
          } as any);
        } else {
          // If simulating and this is a new candle without volume, start with seed volume
          if (simulateVolume && (candle as any).volume === undefined) {
            (candle as any).volume = Math.random() * 0.2 + 0.1;
          }
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

    const sanitizeAndClamp = (arr: CandlestickData[], simulateVolume = false) => {
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
      const cleaned = makeAscendingUnique(aligned, simulateVolume);
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
        let out = sanitizeAndClamp(seed, true);
        seed.length = 0;
        seed.push(...out);

        // Update latestTimeRef when seed updates
        if (seed.length > 0) {
          latestTimeRef.current = seed[seed.length - 1].time as Time;
          updateButtonPosition();
        }

        try {
          candlestickSeries.setData(seed as any);

          // Update volume histogram with colors matching candle direction
          const volumeData = seed.map((c: any) => ({
            time: c.time,
            value: c.volume || 0,
            color: c.close >= c.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
          }));
          volumeSeries.setData(volumeData);

          // Update Indicators
          const smaData = calculateSMA(seed as any, 20);
          smaSeries.setData(smaData);

          const emaData = calculateEMA(seed as any, 50);
          emaSeries.setData(emaData);

        } catch (e) {
          console.warn('setData failed, retrying sanitized', e);
          const clean = sanitizeAndClamp(seed, true);
          candlestickSeries.setData(clean as any);
          // Retry indicators on clean data
          smaSeries.setData(calculateSMA(clean as any, 20));
          emaSeries.setData(calculateEMA(clean as any, 50));
        }
      }

      rafIdRef.current = requestAnimationFrame(flush);
      rafIdRef.current = requestAnimationFrame(flush);
    };

    rafIdRef.current = requestAnimationFrame(flush);

    // --- Update Indicators Loop ---
    // Run periodically or hook into flush? 
    // For performance, we can update indicators less frequently or just after seed update.
    // Let's hook into the flush function's "if (hasOlder || normalized.length > 0)" block.
    // Since we can't easily modify the closure of flush defined above without re-writing it, 
    // we'll explicitly look for the place where setData is called in the `flush` replacement below.
    // ACTUAL IMPLEMENTATION: Redefining flush to include indicator updates.
    // (See next chunk for the redefined flush)

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
            latestTimeRef.current = candleData.time as Time;
            updateButtonPosition();
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
              candlestickSeries.setData(sanitizeAndClamp(seed, false) as any);
            }

            // Initial button positioning
            if (seed.length > 0) {
              latestTimeRef.current = seed[seed.length - 1].time as Time;
              // Small timeout to allow chart to render/layout before calculating coordinate
              setTimeout(updateButtonPosition, 0);
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

  // Effect to handle toggles
  useEffect(() => {
    if (smaSeriesRef.current) {
      smaSeriesRef.current.applyOptions({ visible: showSMA });
    }
    if (emaSeriesRef.current) {
      emaSeriesRef.current.applyOptions({ visible: showEMA });
    }
  }, [showSMA, showEMA]);

  // Sync showNews ref so event handlers can read the latest value
  useEffect(() => {
    showNewsRef.current = showNews;
  }, [showNews]);

  // Effect to fetch News Markers
  useEffect(() => {
    let isMounted = true;
    const fetchNews = async () => {
      if (!candlestickSeriesRef.current) return;

      // If news is off, clear and return
      if (!showNews) {
        candlestickSeriesRef.current.setMarkers([]);
        return;
      }

      try {
        const API_BASE = (import.meta.env.VITE_API_BASE as string) || 'http://localhost:80';
        const resp = await fetch(`${API_BASE}/api/ai/news?symbol=${symbol}&hours=24`);
        if (!resp.ok) return;
        const data = await resp.json();
        if (!isMounted) return;

        if (data && data.news_list) {
          const markers: SeriesMarker<Time>[] = [];
          newsMapRef.current.clear();

          // Also update the permanent news list if we just fetched
          setNewsList(data.news_list.slice(0, 3));

          data.news_list.forEach((n: any) => {
            let t = Math.floor(new Date(n.timestamp).getTime() / 1000);
            if (intervalSeconds > 0) {
              const remainder = t % intervalSeconds;
              t = t - remainder;
            }
            if (isNaN(t)) return;

            if (!newsMapRef.current.has(t)) {
              newsMapRef.current.set(t, []);
            }
            newsMapRef.current.get(t)?.push(n);
          });

          newsMapRef.current.forEach((items, t) => {
            markers.push({
              time: t as Time,
              position: 'aboveBar',
              color: '#17a2b8',
              shape: 'arrowDown',
              text: items.length > 1 ? `News (${items.length})` : 'News',
              size: 1,
            });
          });

          markers.sort((a, b) => (a.time as number) - (b.time as number));
          if (candlestickSeriesRef.current) {
            candlestickSeriesRef.current.setMarkers(markers);
          }
        }
      } catch (e) {
        console.error('Failed to fetch news markers', e);
      }
    };

    fetchNews();

    return () => { isMounted = false; };
  }, [showNews, symbol, intervalSeconds]); // Re-run if these change

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

              {/* Indicators Legend */}
              <span
                style={{
                  color: showSMA ? '#f1c40f' : '#787b86',
                  marginLeft: 8,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  opacity: showSMA ? 1 : 0.5,
                  textDecoration: showSMA ? 'none' : 'line-through'
                }}
              >
                SMA(20) {showSMA && typeof hover.sma === 'number' ? hover.sma.toFixed(2) : ''}
              </span>
              <span
                style={{
                  color: showEMA ? '#3498db' : '#787b86',
                  marginLeft: 8,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  opacity: showEMA ? 1 : 0.5,
                  textDecoration: showEMA ? 'none' : 'line-through'
                }}
              >
                EMA(50) {showEMA && typeof hover.ema === 'number' ? hover.ema.toFixed(2) : ''}
              </span>

              {/* News Hint */}
              {hover.hasNews && (
                <span style={{ color: '#e67e22', marginLeft: 8, fontWeight: 'bold' }}>
                  Click to read News ⬇
                </span>
              )}
            </>
          ) : (
            <>
              <span style={{ color: '#787b86', marginRight: 8 }}>
                Moving cursor to see data...
              </span>
              <span
                style={{
                  color: showSMA ? '#f1c40f' : '#787b86',
                  marginLeft: 8,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  opacity: showSMA ? 1 : 0.5,
                  textDecoration: showSMA ? 'none' : 'line-through'
                }}
              >
                SMA(20)
              </span>
              <span
                style={{
                  color: showEMA ? '#3498db' : '#787b86',
                  marginLeft: 8,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  opacity: showEMA ? 1 : 0.5,
                  textDecoration: showEMA ? 'none' : 'line-through'
                }}
              >
                EMA(50)
              </span>
            </>
          )}
        </div>

        <style>{`
            .text-up { color: #26a69a; }
            .text-down { color: #ef5350; }
          `}</style>
      </div>
      {/* Lightning News Widget */}
      <div
        ref={buttonContainerRef}
        style={{
          position: 'absolute',
          bottom: '5%', // Lower position in volume pane
          left: 0, // Controlled by JS
          zIndex: 2000,
          display: 'none', // Initially hidden until positioned
          flexDirection: 'column',
          alignItems: 'center', // Center popover relative to button
          pointerEvents: 'none'
        }}
      >
        {/* Popover */}
        {showNewsPopover && (
          <div
            style={{
              pointerEvents: 'auto',
              marginBottom: 10,
              width: 320,
              maxHeight: 400,
              backgroundColor: '#1E222D',
              border: '1px solid #2B2F3A',
              borderRadius: 6,
              boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}
          >
            {/* Header */}
            <div style={{
              padding: '12px 16px',
              borderBottom: '1px solid #2B2F3A',
              color: '#17a2b8',
              fontWeight: 600,
              fontSize: 14,
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}>
              <span>📰</span> Relevant News
            </div>

            {/* List */}
            <div style={{ overflowY: 'auto', flex: 1 }}>
              {newsList.length === 0 ? (
                <div style={{ padding: 16, color: '#787b86', fontSize: 13, textAlign: 'center' }}>
                  No recent news found for {symbol}
                </div>
              ) : (
                newsList.map((news) => (
                  <div
                    key={news.news_id}
                    onClick={() => navigate(`/news?symbol=${symbol}&newsId=${encodeURIComponent(news.news_id)}`)}
                    style={{
                      padding: '12px 16px',
                      borderBottom: '1px solid #2B2F3A',
                      cursor: 'pointer',
                      transition: 'background 0.2s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2A2E39'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <div style={{ color: '#EAECEF', fontSize: 13, marginBottom: 4, lineHeight: '1.4' }}>
                      {news.title}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
                      <div style={{ color: '#787b86', fontSize: 11 }}>
                        {new Date(news.timestamp).toLocaleString()}
                      </div>
                      {news.url && (
                        <a
                          href={news.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: '#3498db', fontSize: 11, textDecoration: 'none', fontWeight: 500 }}
                          onClick={(e) => e.stopPropagation()}
                          title="Read original source"
                        >
                          Source ↗
                        </a>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            <div
              onClick={() => navigate(`/news?symbol=${symbol}`)}
              style={{
                padding: '10px',
                textAlign: 'center',
                borderTop: '1px solid #2B2F3A',
                color: '#3498db',
                fontSize: 12,
                cursor: 'pointer',
                fontWeight: 500,
                backgroundColor: '#1E222D',
                pointerEvents: 'auto'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2A2E39'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#1E222D'}
            >
              See More Events ➜
            </div>
          </div>
        )}

        {/* Button */}
        <button
          onClick={() => setShowNewsPopover(!showNewsPopover)}
          style={{
            pointerEvents: 'auto',
            width: 24,
            height: 24,
            borderRadius: '50%',
            backgroundColor: showNewsPopover ? '#2A2E39' : '#1E222D', // Subtle dark change
            border: showNewsPopover ? '1px solid #17a2b8' : '1px solid #2B2F3A',
            color: '#17a2b8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: 12,
            lineHeight: 1, // Ensure vertical centering
            padding: 0,    // Remove browser default padding
            transition: 'all 0.2s',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
          }}
          title="Related News"
        >
          📰
        </button>
      </div>

      {/* Interval News Modal (Click on Marker) */}
      {intervalNews.visible && (
        <div
          style={{
            position: 'absolute',
            top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 10000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          onClick={() => setIntervalNews(prev => ({ ...prev, visible: false }))}
        >
          <div
            style={{
              width: 320,
              maxHeight: '80%',
              backgroundColor: '#1E222D',
              border: '1px solid #2B2F3A',
              borderRadius: 8,
              boxShadow: '0 8px 16px rgba(0,0,0,0.4)',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{
              padding: '12px 16px',
              borderBottom: '1px solid #2B2F3A',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: '#2A2E39'
            }}>
              <div style={{ color: '#17a2b8', fontWeight: 600, fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>📰</span> News in Interval
              </div>
              <button
                onClick={() => setIntervalNews(prev => ({ ...prev, visible: false }))}
                style={{ background: 'none', border: 'none', color: '#787b86', cursor: 'pointer', fontSize: 16 }}
              >
                ✕
              </button>
            </div>

            {/* Time Range Info */}
            <div style={{
              padding: '8px 16px',
              fontSize: 11,
              color: '#787B86',
              borderBottom: '1px solid #2B2F3A',
              backgroundColor: '#1E222D'
            }}>
              Period: <span style={{ color: '#d1d4dc' }}>{intervalNews.rangeLabel}</span>
            </div>

            {/* List */}
            <div style={{ overflowY: 'auto', flex: 1, padding: 0 }}>
              {intervalNews.items.map((news) => (
                <div
                  key={news.news_id}
                  onClick={() => navigate(`/news?symbol=${symbol}&newsId=${encodeURIComponent(news.news_id)}`)}
                  style={{
                    padding: '12px 16px',
                    borderBottom: '1px solid #2B2F3A',
                    cursor: 'pointer',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2A2E39'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <div style={{ color: '#EAECEF', fontSize: 13, marginBottom: 4, lineHeight: '1.4' }}>
                    {news.title}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
                    <div style={{ color: '#787b86', fontSize: 11 }}>
                      {new Date(news.timestamp).toLocaleString()}
                    </div>
                    {news.url && (
                      <a
                        href={news.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#3498db', fontSize: 11, textDecoration: 'none', fontWeight: 500 }}
                        onClick={(e) => e.stopPropagation()}
                        title="Read original source"
                      >
                        Source ↗
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
