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

    # 2. Check your Symbol Name (XAUUSD, GOLD, XAUUSD.pro, etc.)
    symbol = "XAUUSD" 
    
    # 3. Determine if we are Buying or Selling
    trade_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if action == "BUY" else mt5.symbol_info_tick(symbol).bid

    # 4. Build the Request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": trade_type,
        "price": price,
        "sl": float(sl),
        "tp": float(tp),
        "magic": 123456,
        "comment": "Gold Bot Telegram",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # 5. Send to Broker
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Trade Failed! Error Code: {result.retcode}")
    else:
        print(f"✅ SUCCESS: Gold {action} opened at {result.price}")