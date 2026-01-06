import React from 'react';
import './MetricsPanel.css';

interface Props {
  messagesPerSec: number;
  bufferSize: number;
  dropped: number;
  fps: number;
}

export const MetricsPanel: React.FC<Props> = ({ messagesPerSec, bufferSize, dropped, fps }) => {
  return (
    <div className="metrics-panel">
      <div className="metrics-row"><strong>Msgs/s:</strong> <span>{messagesPerSec}</span></div>
      <div className="metrics-row"><strong>Buffer:</strong> <span>{bufferSize}</span></div>
      <div className="metrics-row"><strong>Dropped:</strong> <span>{dropped}</span></div>
      <div className="metrics-row"><strong>FPS:</strong> <span>{fps}</span></div>
    </div>
  );
};
