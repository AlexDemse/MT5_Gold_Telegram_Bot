import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

load_dotenv()

def place_gold_trade(action, entry, sl, tp, lot=0.01):
    # 1. Connect to your MT5 Account
    if not mt5.initialize(
        login=int(os.getenv('MT5_LOGIN')),
        password=os.getenv('MT5_PASSWORD'),
        server=os.getenv('MT5_SERVER')
    ):
        print("MT5 Initialization failed!")
        return

    # 2. Set Symbol
    symbol = "XAUUSDm" 
    
    # Force MT5 to "see" the symbol in Market Watch
    if not mt5.symbol_select(symbol, True):
        print(f"Error: Symbol {symbol} not found or not visible!")
        mt5.shutdown()
        return

    # 3. Get the latest price (Tick)
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"Error: Could not get tick data for {symbol}.")
        mt5.shutdown()
        return

    # 4. Use the tick data safely
    price = tick.ask if action == "BUY" else tick.bid
    trade_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL

    # 5. Build the Request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(lot),
        "type": trade_type,
        "price": float(price),
        "sl": float(sl),
        "tp": float(tp),
        "magic": 123456,
        "comment": "Gold Bot Telegram",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # 6. Send to Broker
    result = mt5.order_send(request)
    
    if result is None:
        print("Trade Failed: No response from MT5 (Order Send Error)")
    elif result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Trade Failed! Error Code: {result.retcode} - {result.comment}")
    else:
        print(f"✅ SUCCESS: Gold {action} opened at {result.price}")

    # Don't shutdown if you want to keep the connection lightning fast, 
    # but for testing, it's safer to close it.
    mt5.shutdown()