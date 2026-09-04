from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import numpy as np

from strategy.signals import generate_prediction_signal

def get_mock_market_data(num_bars=100):
    """Generates synthetic price data for testing predictions."""
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=num_bars, freq="1h")
    price_changes = np.random.normal(loc=0, scale=0.0005, size=num_bars)
    close_prices = 1.0850 + np.cumsum(price_changes)
    
    return pd.DataFrame({
        "timestamp": dates,
        "close": close_prices
    })

def dashboard_index(request):
    """Renders the main dashboard page with updated prediction metrics."""
    symbol = request.GET.get('symbol', 'EURUSD')
    df = get_mock_market_data()
    
    prediction = generate_prediction_signal(df, symbol=symbol)

    context = {
        'prediction': prediction,
        'symbol': symbol,
    }
    return render(request, 'dashboard/index.html', context)

def api_prediction(request):
    """API endpoint returning JSON predictions for dynamic frontend updates."""
    symbol = request.GET.get('symbol', 'EURUSD')
    df = get_mock_market_data()
    
    prediction = generate_prediction_signal(df, symbol=symbol)
    return JsonResponse(prediction)