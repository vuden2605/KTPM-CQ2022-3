import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import type { CandlestickData, Time } from 'lightweight-charts';

interface CandlestickChartProps {
  symbol: string;
}

export const CandlestickChart = ({ symbol }: CandlestickChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const mockIntervalRef = useRef<number | null>(null);
  const websocketOpenedRef = useRef(false);

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

    window.addEventListener('resize', handleResize);

    // Helper: generate mock historical candles
    const generateMockCandles = (count: number, base = 1000) => {
      const now = Math.floor(Date.now() / 1000);
      const candles: CandlestickData[] = [];
      let lastClose = base;
      for (let i = count - 1; i >= 0; i--) {
        const time = now - i * 60 * 60 * 24; // daily
        const open = +(lastClose + (Math.random() - 0.5) * base * 0.02).toFixed(2);
        const high = +(Math.max(open, lastClose) + Math.random() * base * 0.01).toFixed(2);
        const low = +(Math.min(open, lastClose) - Math.random() * base * 0.01).toFixed(2);
        const close = +(low + Math.random() * (high - low)).toFixed(2);
        candles.push({ time: time as Time, open, high, low, close });
        lastClose = close;
      }
      return candles;
    };

    // seed with mock data so chart shows something immediately
    const seed = generateMockCandles(80, 56900);
    candlestickSeries.setData(seed as any);

    // Connect to WebSocket
    const websocket = new WebSocket(`ws://localhost:8083/ws`);

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
          candlestickSeries.update(candleData as any);
          seed.push(candleData);
        } catch (e) {
          console.error('mock update error', e);
        }
      }, 1500);
    };

    websocket.onopen = () => {
      console.log('WebSocket connected for', symbol);
      websocketOpenedRef.current = true;
      // stop mock updates if running
      if (mockIntervalRef.current) {
        clearInterval(mockIntervalRef.current as number);
        mockIntervalRef.current = null;
      }

      // Send SUBSCRIBE message to backend
      const subscribeMsg = {
        type: 'SUBSCRIBE',
        symbol: symbol,
        interval: '1m'
      };
      websocket.send(JSON.stringify(subscribeMsg));
      console.log('Sent SUBSCRIBE:', subscribeMsg);
    };

    websocket.onmessage = (event) => {
      try {
        const candle = JSON.parse(event.data);
        console.log('Received candle:', candle);

        // Parse backend Candle format: openTime (ISO), open (BigDecimal), etc.
        const timestamp = candle.openTime ? new Date(candle.openTime).getTime() / 1000
          : candle.timestamp ? candle.timestamp / 1000
            : Math.floor(Date.now() / 1000);

        const candleData: CandlestickData = {
          time: Math.floor(timestamp) as Time,
          open: parseFloat(candle.open),
          high: parseFloat(candle.high),
          low: parseFloat(candle.low),
          close: parseFloat(candle.close),
        };
        candlestickSeries.update(candleData as any);
      } catch (error) {
        console.error('Error parsing candle data:', error, event.data);
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      startMockUpdates();
    };

    websocket.onclose = () => {
      console.log('WebSocket closed for', symbol);
      websocketOpenedRef.current = false;
      startMockUpdates();
    };

    // Fallback: if websocket not opened in 700ms, start mock updates
    setTimeout(() => {
      if (!websocketOpenedRef.current) startMockUpdates();
    }, 700);

    // no need to keep websocket in state for now

    return () => {
      window.removeEventListener('resize', handleResize);
      websocket.close();
      chart.remove();
      if (mockIntervalRef.current) {
        clearInterval(mockIntervalRef.current as number);
        mockIntervalRef.current = null;
      }
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
    />
  );
};
