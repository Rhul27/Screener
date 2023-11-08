import ccxt
import pandas as pd
import asyncio

# Initialize the exchange
exchange = ccxt.binance()

# Define indicator parameters
rsi_period = 14
macd_fast_period = 12
macd_slow_period = 26
macd_signal_period = 9
ema_period = 21
ma_period = 55

# Define a function to calculate RSI
def calculate_rsi(df, period):
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Define a function to calculate MACD
def calculate_macd(df, fast_period, slow_period, signal_period):
    exp1 = df['close'].ewm(span=fast_period, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow_period, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    return macd, signal

# Define a function to calculate EMA
def calculate_ema(df, period):
    ema = df['close'].ewm(span=period, adjust=False).mean()
    return ema

# Define a function to calculate MA
def calculate_ma(df, period):
    ma = df['close'].rolling(window=period).mean()
    return ma

# Define a function to calculate the signal for a symbol
async def calculate_signal(symbol):
    # Fetch historical OHLCV data for 1-hour timeframe
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)

    # Create a Pandas DataFrame for the data
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Calculate RSI
    rsi = calculate_rsi(df, rsi_period)

    # Calculate MACD
    macd, signal = calculate_macd(df, macd_fast_period, macd_slow_period, macd_signal_period)

    # Calculate EMA
    ema = calculate_ema(df, ema_period)

    # Calculate MA
    ma = calculate_ma(df, ma_period)

    # Initialize counters for signal categories
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0

    # Determine the signals based on individual indicators
    if rsi.iloc[-1] >= 70:
        bearish_count += 1
    elif rsi.iloc[-1] <= 30:
        bullish_count += 1
    else:
        neutral_count +=1

    if macd.iloc[-1] > signal.iloc[-1]:
        bearish_count += 1
    elif macd.iloc[-1] < signal.iloc[-1] and 0 > signal.iloc[-1]:
        bullish_count += 1
    else :
        neutral_count+=1

    

    if df['close'].iloc[-1] > ema.iloc[-1]:
        bullish_count += 1
    elif df['close'].iloc[-1] < ema.iloc[-1]:
        bearish_count += 1
    else:
        neutral_count+=1

    if ma.iloc[-1] > df['close'].iloc[-1]:
        bearish_count += 1
    elif ma.iloc[-1] < df['close'].iloc[-1]:
        bullish_count += 1  
    else:
        neutral_count+=1


    data={
        'Symbol':symbol,
        'Bullish':bullish_count,
        'Bearish':bearish_count,
        'Neutral':neutral_count
    }

    if bullish_count>bearish_count and bullish_count>=neutral_count:
        if bullish_count == 4:
            data['Signal']='Strong Buy'
            return data
        else :
            data['Signal']='Buy'
            return data
    elif bearish_count > bullish_count and bearish_count>=neutral_count:
         if bearish_count == 4:
            data['Signal']='Strong Sell'
            return data
         else :
            data['Signal']='Sell'
            return data
    elif neutral_count>bullish_count and neutral_count>bearish_count:
         if neutral_count == 4:
            data['Signal']='Neutal'
            return data
         else :
            data['Signal']='Neutal'
            return data
    elif bullish_count==bearish_count  :
            data['Signal']='Neutal'
            return data
    # else:
    await asyncio.sleep(1)
    #     return 'Neutral'
        

