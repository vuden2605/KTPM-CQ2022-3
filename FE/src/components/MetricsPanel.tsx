import React from 'react';
import '../styles/MetricsPanel.css';

interface Props {
  messagesPerSec: number;
  bufferSize: number;
  dropped: number;
  fps: number;
}

export const MetricsPanel: React.FC<Props> = ({ messagesPerSec, bufferSize, dropped, fps }) => {
  return (
    <div style={{
      position: 'absolute',
      right: 80, /* Shifted left to avoid covering chart Y-axis */
      top: 10,
      zIndex: 40,
      display: 'flex',
      gap: 12,
      fontSize: 12,
      fontFamily: 'JetBrains Mono, monospace',
      color: '#787b86',
      pointerEvents: 'none'
    }}>
      <div style={{ display: 'flex', gap: 4 }}><span>Msgs/s:</span><span style={{ color: '#d1d4dc' }}>{messagesPerSec}</span></div>
      <div style={{ display: 'flex', gap: 4 }}><span>Buffer:</span><span style={{ color: '#d1d4dc' }}>{bufferSize}</span></div>
      <div style={{ display: 'flex', gap: 4 }}><span>Drop:</span><span style={{ color: dropped > 0 ? '#ef5350' : '#d1d4dc' }}>{dropped}</span></div>
      <div style={{ display: 'flex', gap: 4 }}><span>FPS:</span><span style={{ color: '#d1d4dc' }}>{fps}</span></div>
    </div>
  );
};
