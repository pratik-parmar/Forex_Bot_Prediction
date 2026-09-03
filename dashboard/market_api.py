from django.http import JsonResponse
from django.core.cache import cache
import requests
import datetime

def market_candles(request):
    timeframe = request.GET.get('timeframe', '15m')
    cache_key = f"xauusd_candles_{timeframe}"
    
    # Return cached response if available (avoids hitting API limits)
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    api_key = "301854d2ec5a4235810527169876c5fb"
    
    interval_map = {
        '1m': '1min', '5m': '5min', '15m': '15min',
        '30m': '30min', '1h': '1h', '4h': '4h', '1d': '1day'
    }
    interval = interval_map.get(timeframe, '15min')
    
    url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval={interval}&outputsize=100&apikey={api_key}"

    try:
        response = requests.get(url).json()

        if "values" not in response:
            return JsonResponse({'error': response.get('message', 'API Limit Reached or Invalid Key')}, status=429)

        candles = []
        for row in reversed(response["values"]):
            dt = datetime.datetime.strptime(row['datetime'], "%Y-%m-%d %H:%M:%S" if len(row['datetime']) > 10 else "%Y-%m-%d")
            candles.append({
                'time': int(dt.timestamp()),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            })

        data = {
            'symbol': 'XAUUSD',
            'timeframe': timeframe,
            'candles': candles
        }

        # Cache the result for 60 seconds
        cache.set(cache_key, data, timeout=60)
        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)