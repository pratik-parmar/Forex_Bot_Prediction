from data.market_data import get_forex_data
from strategy.indicators import calculate_indicators
from strategy.signals import generate_signal
from strategy.risk_manager import (
    calculate_risk,
    calculate_stop_loss,
    calculate_take_profit
)


print("Forex Trading Bot Started")


# --------------------------------------------------
# 1. Get XAUUSD market data
# --------------------------------------------------

data = get_forex_data(
    symbol="GC=F",
    period="5d",
    interval="15m"
)


# --------------------------------------------------
# 2. Calculate technical indicators
# --------------------------------------------------

data = calculate_indicators(data)


# --------------------------------------------------
# 3. Generate trading signal
# --------------------------------------------------

signal = generate_signal(data)


# --------------------------------------------------
# 4. Get latest market data
# --------------------------------------------------

latest = data.iloc[-1]

price = float(latest["Close"])
ema20 = float(latest["EMA_20"])
ema50 = float(latest["EMA_50"])
rsi = float(latest["RSI_14"])
atr = float(latest["ATR_14"])


# --------------------------------------------------
# 5. Account settings
# --------------------------------------------------

account_balance = 150
risk_percent = 1


# --------------------------------------------------
# 6. Calculate maximum risk
# --------------------------------------------------

risk_amount = calculate_risk(
    account_balance,
    risk_percent
)


# --------------------------------------------------
# 7. Calculate Stop Loss
# --------------------------------------------------

stop_loss = calculate_stop_loss(
    price,
    atr,
    signal
)


# --------------------------------------------------
# 8. Calculate Take Profit
# --------------------------------------------------

take_profit = calculate_take_profit(
    price,
    stop_loss,
    signal
)


# --------------------------------------------------
# 9. Display market analysis
# --------------------------------------------------

print("\nLatest market data:")

print("Price:", price)
print("EMA 20:", ema20)
print("EMA 50:", ema50)
print("RSI:", rsi)
print("ATR:", atr)


# --------------------------------------------------
# 10. Display trading signal
# --------------------------------------------------

print("\nTrading Signal:", signal)


# --------------------------------------------------
# 11. Display risk management
# --------------------------------------------------

print("\nRisk Management:")

print("Account Balance: $", account_balance)
print("Risk Percent:", risk_percent, "%")
print("Maximum Risk: $", risk_amount)


# --------------------------------------------------
# 12. Display Stop Loss and Take Profit
# --------------------------------------------------

if stop_loss is not None:

    print("Stop Loss:", stop_loss)
    print("Take Profit:", take_profit)

    risk_distance = abs(price - stop_loss)

    reward_distance = abs(take_profit - price)

    risk_reward = reward_distance / risk_distance

    print("Risk Distance:", risk_distance)
    print("Reward Distance:", reward_distance)
    print("Risk/Reward: 1:", risk_reward)

else:

    print("Stop Loss: Not calculated because signal is HOLD")
    print("Take Profit: Not calculated because signal is HOLD")