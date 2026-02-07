import type { LineData, Time } from 'lightweight-charts';

interface InputCandle {
  time: Time;
  close: number;
}

/**
 * Calculates Simple Moving Average (SMA)
 * @param data Array of candles (must be sorted by time)
 * @param period The SMA period (e.g., 20)
 */
export const calculateSMA = (data: InputCandle[], period: number): LineData[] => {
  const result: LineData[] = [];
  if (data.length < period) return result;

  for (let i = period - 1; i < data.length; i++) {
    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close;
    }
    result.push({
      time: data[i].time,
      value: sum / period,
    });
  }
  return result;
};

/**
 * Calculates Exponential Moving Average (EMA)
 * @param data Array of candles (must be sorted by time)
 * @param period The EMA period (e.g., 50)
 */
export const calculateEMA = (data: InputCandle[], period: number): LineData[] => {
  const result: LineData[] = [];
  if (data.length < period) return result;

  // Initial SMA as the first EMA point
  let sum = 0;
  for (let j = 0; j < period; j++) {
    sum += data[period - 1 - j].close;
  }
  let prevEma = sum / period;

  result.push({
    time: data[period - 1].time,
    value: prevEma,
  });

  const multiplier = 2 / (period + 1);

  for (let i = period; i < data.length; i++) {
    const close = data[i].close;
    const currentEma = (close - prevEma) * multiplier + prevEma;
    result.push({
      time: data[i].time,
      value: currentEma,
    });
    prevEma = currentEma;
  }

  return result;
};
