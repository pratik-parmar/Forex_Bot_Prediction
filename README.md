# Demo :- https://forex-bot-prediction.onrender.com/

# Forex Trading Dashboard

Overview

Forex Trading Dashboard is a Django-based web application for monitoring financial markets, visualizing price movements, analyzing technical indicators, and generating rule-based trading signals.

The application integrates TradingView charts with a Python backend that retrieves market candle data and calculates technical indicators. It also includes user authentication with email OTP verification, using Brevo's HTTPS transactional email API.

The project is designed as a market analysis and decision-support tool. Trading signals are informational and do not automatically execute trades.

Tech Stack
Component	Technology
Backend	Python, Django
Frontend	HTML5, CSS3, JavaScript (Vanilla ES6+)
Charting	TradingView Widget
Market Data	Finnhub API / Yahoo Finance (where configured)
Technical Analysis	Pandas, Python-based indicator calculations
Authentication	Django Session Authentication
Email Verification	Brevo Transactional Email API (HTTPS)
Real-Time Communication	Django Channels, WebSockets
Database	SQLite
ASGI Server	Daphne
Static Files	WhiteNoise
Deployment	Render
Features
Market Dashboard
Interactive TradingView chart integration.
Supported market symbols include XAUUSD, EURUSD, GBPUSD, and BTCUSD.
Multiple timeframe options: 1m, 5m, 15m, 30m, 1H, and 1D.
Market candle retrieval through backend data integrations.
Responsive dashboard with dark/light theme support.
Technical Analysis

The backend calculates technical indicators, including:

Exponential Moving Average (EMA 20 and EMA 50)
Relative Strength Index (RSI 14)
Average True Range (ATR 14)
Moving Average Convergence Divergence (MACD)
Bollinger Bands
Trading Signals
Rule-based BUY, SELL, and HOLD signals.
Signal reasoning and condition details.
Entry, Stop Loss (SL), and Take Profit (TP) calculations.
Risk-based analysis parameters.

Signals are generated for analysis purposes and are not guaranteed to be profitable.

Authentication & Email Verification
User registration and login.
Django session-based authentication.
Email OTP verification before account activation.
Secure OTP hashing and expiration.
Maximum OTP verification attempts.
OTP resend cooldown.
Brevo HTTPS API integration for email delivery.
Logout functionality.
Backend API
Technical-analysis endpoint for supported symbols and timeframes.
JSON responses containing analysis results.
Authentication protection for the technical-analysis API.
Project Structure
Forex_Bot_Prediction/
│
├── config/
├── dashboard/
│   ├── migrations/
│   ├── templates/
│   │   └── dashboard/
│   ├── forms.py
│   ├── models.py
│   ├── views.py
│   ├── technical.py
│   ├── urls.py
│   └── ...
│
├── data/
│   └── market_data.py
│
├── strategy/
│   ├── indicators.py
│   ├── signals.py
│   └── ...
│
├── mutual_funds/
├── forex_web/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── ...
│
├── manage.py
├── requirements.txt
├── build.sh
├── .env.example
├── .gitignore
└── README.md
Getting Started Locally
Prerequisites
Python 3.11+ (Python 3.13 recommended if supported by your dependencies)
Git
Finnhub API key for configured market-data integrations
Brevo API key and a verified sender email for email OTP delivery
1. Clone the Repository
git clone https://github.com/pratik-parmar6004/Forex_Bot_Prediction.git

cd Forex_Bot_Prediction
2. Create a Virtual Environment

macOS / Linux

python3 -m venv .venv
source .venv/bin/activate

Windows

python -m venv .venv
.venv\Scripts\activate
3. Install Dependencies
pip install -r requirements.txt
4. Configure Environment Variables

Create a .env file in the project root.

# Django
DJANGO_SECRET_KEY=your_django_secret_key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=

# Market Data
FINNHUB_API_KEY=your_finnhub_api_key

# Brevo HTTPS Transactional Email API
BREVO_API_KEY=your_brevo_api_key
BREVO_SENDER_EMAIL=your_verified_sender@example.com
BREVO_SENDER_NAME=Forex Terminal

Replace the placeholder values with your own credentials.

Do not commit .env or expose API keys, passwords, or Django secret keys in GitHub.

The OTP email implementation uses Brevo's HTTPS API. SMTP credentials are not required for this email flow.

5. Apply Database Migrations
python manage.py migrate
6. Create a Superuser (Optional)
python manage.py createsuperuser
7. Run the Development Server
python manage.py runserver

Open:

http://127.0.0.1:8000/

For local ASGI/WebSocket testing, you can also run Daphne:

daphne -b 127.0.0.1 -p 8000 forex_web.asgi:application
API Usage
Technical Analysis

Endpoint

GET /api/technical-analysis/

Example request

GET /api/technical-analysis/?symbol=XAUUSD&timeframe=15

Supported symbols:

XAUUSD
EURUSD
GBPUSD
BTCUSD

Supported timeframes:

Value	Interval
1	1 minute
5	5 minutes
15	15 minutes
30	30 minutes
60	1 hour
D	1 day

The endpoint returns JSON analysis data, including the symbol, timeframe, technical-analysis results, and a success status.

The endpoint is protected by the application's authentication decorator, so an authenticated session may be required.

Email OTP Verification

The registration process follows this flow:

A user submits the registration form.
Django creates an inactive user account.
A secure six-digit OTP is generated and hashed.
The OTP is sent through Brevo's HTTPS transactional email API.
The user enters the OTP on the verification page.
Django validates the OTP and expiration.
The account is activated after successful verification.
OTP Security
OTP is stored as a hash rather than plaintext.
OTP expires after 10 minutes.
Maximum of 5 verification attempts.
Resend cooldown of 60 seconds.
Failed email delivery invalidates the OTP while keeping the account inactive for a resend attempt.

Brevo API credentials and sender configuration must be set in the deployment environment.

Deployment on Render

This project is deployed as a Django Web Service on Render.

Deployment Configuration
Setting	Value
Runtime	Python
Branch	main
Build Command	pip install -r requirements.txt
Start Command	daphne -b 0.0.0.0 -p $PORT forex_web.asgi:application

Configure the required environment variables in:

Render Dashboard → Your Web Service → Environment

DJANGO_SECRET_KEY=your_production_secret_key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=forex-bot-prediction.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://forex-bot-prediction.onrender.com

FINNHUB_API_KEY=your_finnhub_api_key

BREVO_API_KEY=your_brevo_api_key
BREVO_SENDER_EMAIL=your_verified_sender@example.com
BREVO_SENDER_NAME=Forex Terminal

Use your actual secret values in Render. Never add them to this README or commit them to GitHub.

Ensure database migrations are applied during deployment using your deployment workflow or Render Shell:

python manage.py migrate

Note: Render Free services may have ephemeral local filesystems and can spin down when idle. SQLite data may not persist across service replacements or redeployments. For persistent production user accounts, configure a persistent database such as PostgreSQL.

Security Considerations
Keep API keys and secret keys in environment variables.
Keep Django DEBUG=False in production.
Configure allowed hosts and CSRF trusted origins for the deployed domain.
Use HTTPS for production traffic.
Use authenticated access for protected dashboard and API views.
Do not expose OTPs, passwords, or API credentials in application logs.
Future Enhancements

PostgreSQL integration for persistent production data.

Expand technical-analysis strategies and backtesting.

Add more currency pairs and market instruments.

Improve market-data caching and API rate-limit handling.

Add signal notifications.

Add automated tests for authentication, OTP verification, and analysis APIs.

Explore MetaTrader 5 integration for trade execution through a secure bridge.

Disclaimer

This application is intended for educational, analytical, and informational purposes only. Trading signals and technical indicators are not financial advice and do not guarantee future market performance. Always perform independent research and risk assessment before making trading decisions.

Author

Pratik Parmar
