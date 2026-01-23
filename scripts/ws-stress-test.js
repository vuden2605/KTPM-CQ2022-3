/**
 * WebSocket Stress Test Script (k6)
 * 
 * This script tests WebSocket connections using STOMP protocol.
 * It ramps up from 1,000 → 5,000 → 10,000 concurrent users.
 * 
 * REQUIREMENTS:
 *   - Docker must be running
 *   - All services must be up: docker-compose up -d
 * 
 * HOW TO RUN (using Docker - recommended):
 *   docker run --rm -i --network ktpm-cq2022-3_crypto-network grafana/k6 run - < scripts/ws-stress-test.js
 * 
 * CUSTOM VU COUNT (override stages):
 *   docker run --rm -i --network ktpm-cq2022-3_crypto-network grafana/k6 run --vus 5000 --duration 1m - < scripts/ws-stress-test.js
 * 
 * EXAMPLE QUICK TESTS:
 *   1k users:  docker run --rm -i --network ktpm-cq2022-3_crypto-network grafana/k6 run --vus 1000 --duration 30s - < scripts/ws-stress-test.js
 *   5k users:  docker run --rm -i --network ktpm-cq2022-3_crypto-network grafana/k6 run --vus 5000 --duration 30s - < scripts/ws-stress-test.js
 *   10k users: docker run --rm -i --network ktpm-cq2022-3_crypto-network grafana/k6 run --vus 10000 --duration 30s - < scripts/ws-stress-test.js
 */

import ws from 'k6/ws';
import { sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// Custom Metrics
const connectedUsers = new Counter('connected_users');
const messageCount = new Counter('received_messages');
const connectionErrors = new Counter('connection_errors');
const connectTime = new Trend('connect_time');

// Test Configuration
export const options = {
  // Define stages to simulate ramping up traffic
  stages: [
    { duration: '30s', target: 1000 },  // Ramp up to 1000 users
    { duration: '1m', target: 1000 },   // Stay at 1000
    { duration: '30s', target: 5000 },  // Ramp up to 5000
    { duration: '1m', target: 5000 },   // Stay at 5000
    { duration: '30s', target: 10000 }, // Ramp up to 10000!
    { duration: '1m', target: 10000 },  // Stay at 10000
    { duration: '30s', target: 0 },     // Scale down
  ],
};

// Use 'nginx' when running k6 inside Docker network
// Use 'localhost' when running k6 on Windows directly
const url = __ENV.WS_URL || 'ws://nginx/ws';

export default function () {
  const params = { tags: { my_tag: 'ws-stress' } };
  const startTime = Date.now();

  const res = ws.connect(url, params, function (socket) {
    socket.on('open', function open() {
      // 1. Send STOMP CONNECT Frame
      const connectFrame = 'CONNECT\naccept-version:1.2,1.1,1.0\nheart-beat:10000,10000\n\n\0';
      socket.send(connectFrame);
    });

    socket.on('message', function (data) {
      // 2. Handle STOMP responses
      if (data.startsWith('CONNECTED')) {
        // Connected successfully
        const latency = Date.now() - startTime;
        connectTime.add(latency);
        connectedUsers.add(1);

        // 3. Subscribe to Topic
        const subscribeFrame = 'SUBSCRIBE\nid:sub-0\ndestination:/topic/candle.BTCUSDT.1m\n\n\0';
        socket.send(subscribeFrame);
      } else if (data.startsWith('MESSAGE')) {
        // Received broadcast message
        messageCount.add(1);
      } else if (data.startsWith('ERROR')) {
        console.error('STOMP Error: ' + data);
      }
    });

    socket.on('close', function () {
      // console.log('Disconnected');
    });

    socket.on('error', function (e) {
      connectionErrors.add(1);
      // console.error('WebSocket Error: ' + e.error());
    });

    // Keep connection alive for a random duration between 30s and 60s
    // to simulate real user session overlap during ramp-up
    sleep(Math.random() * 30 + 30);
  });

  // Note: ws.connect() in k6 doesn't return a response object like HTTP
  // Success is tracked via the 'connected_users' custom metric
}
