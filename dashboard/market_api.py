from django.http import JsonResponse
import yfinance as yf

def market_candles(request):
    timeframe = request.GET.get('timeframe', '2m')
    
    tf_map = {
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '60m',
        '1d': '1d',
    }
    interval = tf_map.get(timeframe, '15m')
    
    # Gold Futures symbol (XAUUSD equivalent)
    ticker = yf.Ticker("GC=F") 
    df = ticker.history(period="5d", interval=interval)
    
    if df.empty:
        return JsonResponse({'error': 'No candle data retrieved'}, status=400)
    
    candles = [
        {
            'time': int(index.timestamp()),
            'open': round(float(row['Open']), 2),
            'high': round(float(row['High']), 2),
            'low': round(float(row['Low']), 2),
            'close': round(float(row['Close']), 2),
        }
        for index, row in df.iterrows()
    ]
        
    return JsonResponse({
        'symbol': 'XAUUSD',
        'timeframe': timeframe,
        'candles': candles
    })