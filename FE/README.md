# Trading Chart Frontend

React + TypeScript frontend application for displaying real-time cryptocurrency and stock candlestick charts.

## Features

- 📊 Real-time candlestick charts using lightweight-charts
- 📈 Watchlist with multiple symbols (VCB, BTCUSD, ETHUSD, etc.)
- 🔌 WebSocket connection to backend for live data
- 🎨 Dark theme UI similar to TradingView
- ⚡ Built with Vite for fast development

## Prerequisites

- Node.js 18+ 
- Backend services running:
  - Redis (port 6379)
  - ingest-service (port 8081)
  - ws-service (port 8083)

## Installation

```bash
cd FE
npm install
```

## Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Build

```bash
npm run build
```

## Project Structure

```
FE/
├── src/
│   ├── components/
│   │   ├── CandlestickChart.tsx   # Main chart component
│   │   ├── Watchlist.tsx          # Symbol watchlist sidebar
│   │   └── Watchlist.css          # Watchlist styles
│   ├── App.tsx                    # Main app layout
│   ├── App.css                    # App styles
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Global styles
├── package.json
└── vite.config.ts
```

## WebSocket Connection

The chart connects to `ws://localhost:8083/ws/candles/{symbol}` to receive real-time candlestick data.

Expected candle data format:
```json
{
  "timestamp": 1703347200000,
  "open": 56900,
  "high": 57100,
  "low": 56800,
  "close": 57000
}
```

## Customization

### Adding New Symbols

Edit the `symbols` array in `src/components/Watchlist.tsx`:

```typescript
const [symbols] = useState<Symbol[]>([
  { code: 'YOUR_SYMBOL', name: 'Symbol Name', price: 0, change: 0, changePercent: 0, type: 'stock' },
  // ...
]);
```

### Chart Styling

Customize chart colors in `src/components/CandlestickChart.tsx`:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
