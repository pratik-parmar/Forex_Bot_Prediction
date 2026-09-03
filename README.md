# Demo :- https://forex-bot-prediction.onrender.com/

# Forex Trading Dashboard

An interactive, real-time Forex Trading Dashboard built for monitoring **XAUUSD (Gold / US Dollar)** market movement, viewing technical indicators, receiving automated trade signals, and executing trades.

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![TradingView](https://img.shields.io/badge/TradingView-131722?style=for-the-badge&logo=tradingview&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

---

## Tech Stack

- **Frontend Interface:** HTML5, CSS3, JavaScript (Vanilla ES6+)
- **Charting Engine:** TradingView Widget Integration (`OANDA:XAUUSD`)
- **Backend API Support (Optional):**  Python backend supporting historical candles via `/api/market-candles/`
- **Hosting & Deployment:** Render

---

## Features

- **Embedded TradingView Charting**: Advanced charting powered by TradingView widgets with real-time price updates for gold markets.
- **Dynamic Timeframe Switching**: Seamlessly switch between `1m`, `5m`, `15m`, `30m`, `1H`, and `1D` intervals with auto-syncing UI badges.
- **Automated Technical Indicators**: Real-time calculation for:
  - Exponential Moving Averages (**EMA 20** & **EMA 50**)
  - Relative Strength Index (**RSI 14**)
  - Average True Range (**ATR 14**)
- **Algorithmic Trading Signals**: Dynamic **BUY**, **SELL**, or **HOLD** indicator signals complete with auto-generated Entry, Stop Loss (SL), and Take Profit (TP) targets.
- **Responsive & Dark/Light Theme**: Built-in theme toggle with responsive breakpoints optimized for mobile, tablet, and desktop viewing.

---

## Getting Started Locally

### Prerequisites
- A modern web browser (Chrome, Firefox, Edge, Safari)
- *Optional:* A local server or backend API running on `localhost` if you are hosting the candlestick data endpoint locally.

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone [https://github.com/your-username/forex-terminal-dashboard.git](https://github.com/your-username/forex-terminal-dashboard.git)
   cd forex-terminal-dashboard


   Deployment on Render
You can easily host this dashboard on Render as a static site or web service.

Method: Deploy as a Static Site (Fastest)
Push your repository to your GitHub account.

Log in to your Render Dashboard.

Click on New + in the top right and select Static Site.

Connect your GitHub repository (forex-terminal-dashboard).

Configure the deployment settings:

Name: forex-trading-dashboard (or your preferred name)

Branch: main (or master)

Build Command: (Leave blank, no build step is required for a pure HTML/JS frontend)

Publish Directory: . (root directory)

Click Create Static Site.

Render will automatically build and deploy your application, providing you with a live URL (e.g., https://forex-trading-dashboard.onrender.com).

File Structure
Plaintext
.
├── index.html       # Single-page frontend containing layout, CSS styling, and client script logic
└── README.md        # Project documentation
Future Enhancements
[ ] Complete MT5 (MetaTrader 5) API integration via Windows VPS bridge for live trade execution.

[ ] Add support for additional currency pairs (EURUSD, GBPUSD, USDJPY).

[ ] Push notifications for new buy/sell signals.
