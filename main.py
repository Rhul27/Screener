from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
import asyncio
import websockets
import json
import time
from sys import path, exc_info
from func import *
from tele import *

'''
Binance Price
Gateio Price
Price Difference 
OrderBook
Bullish/Bearish/Neutral
Crytpo Currency Conversion
'''

app = FastAPI()

symbols = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "MANAUSDT", "OCEANUSDT", "ADAUSDT",
    "SOLUSDT", "XRPUSDT", "DOGEUSDT", "GALAUSDT"
]

last_prices = {
    "binance": {},
    "gateio": {}
}


############################### BINANCE PRICE START ###############################

async def binance_websocket_task(websocket, symbol, data_dict):
    try:
        binance_endpoint = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@trade"
        async with websockets.connect(binance_endpoint) as ws:
            while True:
                try:
                    data = await ws.recv()
                    price = json.loads(data)["p"]
                    data_dict[symbol] = price
                    last_prices["binance"][symbol] = json.loads(data)["p"]
                    formatted_data = [{symbol: price} for symbol, price in data_dict.items()]
                    await websocket.send_json(formatted_data)
                except websockets.exceptions.ConnectionClosed:
                    break
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        # print(f'Type: {exc_type.__name__}\nLine: {exc_tb.tb_lineno}\nError: {e}')
        senderror(f'!!!!ERROR!!!!\n\nProject: Screener\nFolder: ...\nFile: main.py\nFunction: binance_websocket_task\nType: {exc_type.__name__}\nLine: {exc_tb.tb_lineno}\nError: {e}')
        # return JSONResponse({'error':'An error occured'},status_code=400)
        pass

@app.websocket("/binance")
async def binance_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    price_data = {symbol: 0 for symbol in symbols}
    tasks = [binance_websocket_task(websocket, symbol, price_data) for symbol in symbols]
    await asyncio.gather(*tasks)

############################### BINANCE PRICE END ###############################

############################ BINANCE ORDER_BOOK START ###########################

order_books = {symbol: {"bids": [], "asks": []} for symbol in symbols}

async def handle_order_book_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        tasks = [binance_order_book_websocket(websocket, symbol) for symbol in symbols]
        await asyncio.gather(*tasks)
    except websockets.exceptions.ConnectionClosed:
        pass

async def binance_order_book_websocket(websocket: WebSocket, symbol):
    url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@depth"
    async with websockets.connect(url) as ws:
        while True:
            try:
                data = await ws.recv()
                order_book_data = process_order_book_data(json.loads(data), symbol)
                await websocket.send_json(order_book_data)
            except websockets.exceptions.ConnectionClosed:
                break

def process_order_book_data(data, symbol):
    update_id = data['u']
    bids = [{"price": price, "quantity": qty} for price, qty in data['b']]
    asks = [{"price": price, "quantity": qty} for price, qty in data['a']]
    return {"symbol": symbol, "update_id": update_id, "bids": bids, "asks": asks}

@app.websocket("/orderbook")
async def order_book_endpoint(websocket: WebSocket):
    await handle_order_book_websocket(websocket)

############################ BINANCE ORDER_BOOK END ###########################

############################### GATEIO PRICE START ###############################

gateio_currency_pairs = ["BTC_USDT", "ETH_USDT", "BNB_USDT", "MANA_USDT", "OCEAN_USDT", "ADA_USDT", "SOL_USDT", "XRP_USDT", "DOGE_USDT", "GALA_USDT"]

async def gateio_websocket_task(websocket, currency_pair):
    gateio_endpoint = f"wss://api.gateio.ws/ws/v4/"
    async with websockets.connect(gateio_endpoint) as ws:
        subscribe_msg = {
            "time": int(time.time()),
            "channel": "spot.tickers",
            "event": "subscribe",
            "payload": [currency_pair]
        }
        await ws.send(json.dumps(subscribe_msg))
        while True:
            try:
                data = await ws.recv()
                ticker_data = json.loads(data)
                if "event" in ticker_data and ticker_data["event"] == "update":
                    result = ticker_data.get("result", {})
                    currency_pair = result.get("currency_pair")
                    last_price = result.get("last")
                    last_prices["gateio"][currency_pair.replace("_", "")] = last_price
                    await websocket.send_json(result)
            except websockets.exceptions.ConnectionClosed:
                break

@app.websocket("/gateio")
async def gateio_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    tasks = [asyncio.ensure_future(gateio_websocket_task(websocket, symbol)) for symbol in gateio_currency_pairs]
    await asyncio.gather(*tasks)

############################### GATEIO PRICE END ###############################

############################### BINANCE-GATEIO PRICE_DIFFERENCE START ###############################

@app.websocket("/price_difference_gate_binance")
async def price_difference_gate_binance_endpoint(websocket: WebSocket):
    global price_difference_websocket
    price_difference_websocket = websocket
    await websocket.accept()
    try:
        while True:
            if price_difference_websocket is None:
                break

            price_diff_data = []
            for symbol in symbols:
                binance_price = last_prices["binance"].get(symbol, 0)
                gateio_price = last_prices["gateio"].get(symbol, 0)

                price_diff = float(binance_price) - float(gateio_price)
                price_diff_abs = abs(price_diff)
                if gateio_price != 0:
                    price_diff_percentage = (price_diff_abs / float(gateio_price)) * 100
                else:
                    price_diff_percentage = 0

                price_diff_data.append({
                    "Symbol": symbol,
                    "binanceprice": (float(binance_price), 2),
                    "gateprice": (float(gateio_price), 2),  
                    "difference": (price_diff_abs, 6),  
                    "difference_percentage": round(price_diff_percentage, 6)  
                })
            await websocket.send_json(price_diff_data)
            await asyncio.sleep(1)  
    except websockets.exceptions.ConnectionClosed:
            pass
    
############################### BINANCE-GATEIO PRICE_DIFFERENCE END ###############################

################################### API START #######################################

@app.post('/get_signals')
async def get_sig():
    try:
        symbols = [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "MANA/USDT", "OCEAN/USDT",
        "ADA/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT", "GALA/USDT"
                ]
        # Create tasks to calculate signals for each symbol concurrently
        tasks = [calculate_signal(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        signals = [results[i] for i in range(len(symbols))]

        return JSONResponse({'data':signals},status_code=200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        # print(f'Type: {exc_type.__name__}\nLine: {exc_tb.tb_lineno}\nError: {e}')
        senderror(f'!!!!ERROR!!!!\n\nProject: Screener\nFolder: ...\nFile: main.py\nFunction: api get_signals\nType: {exc_type.__name__}\nLine: {exc_tb.tb_lineno}\nError: {e}')
        return JSONResponse({'error':'An error occured'},status_code=400)

@app.post("/convert")
async def convert_crypto(source_crypto: str, amount: float, target_crypto: str):
    try:
        # Fetch cryptocurrency exchange rates from an API (e.g., CoinGecko)
        response = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": source_crypto,
                "vs_currencies": target_crypto,
            },
        )
        data = response.json()
        # print(data)
        
        if source_crypto in data and target_crypto in data[source_crypto]:
            exchange_rate = data[source_crypto][target_crypto]
            converted_amount = amount * exchange_rate
            return {
                "source_crypto": source_crypto,
                "amount": amount,
                "target_crypto": target_crypto,
                "converted_amount": converted_amount,
            }
        else:
            return {"error": "Invalid cryptocurrency symbols"}
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        # print(f'Type: {exc_type.__name__}\nLine: {exc_tb.tb_lineno}\nError: {e}')
        senderror(f'!!!!ERROR!!!!\n\nProject: Screener\nFolder: ...\nFile: main.py\nFunction: api convert_crypto\nType: {exc_type.__name__}\nLine: {exc_tb.tb_lineno}\nError: {e}')
        return JSONResponse({'error':'An error occured'},status_code=400)

################################### API END ######################################


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

