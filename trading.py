import MetaTrader5 as mt5
import os
import config  # This is the bridge to your GUI
from dotenv import load_dotenv

load_dotenv()

def calculate_safety_sl(action, entry_price, risk_dollars, lot):
    # This remains the same, but now uses values passed from config
    if action == "BUY":
        return round(entry_price - (risk_dollars / (lot * 100)), 2)
    else:
        return round(entry_price + (risk_dollars / (lot * 100)), 2)

# Removed 'lot=0.01' from the parentheses because we will fetch it inside
import MetaTrader5 as mt5
import config

def place_gold_trade(action, entry, sl, tp=None):
    if not mt5.initialize():
        return

    # Fetch settings
    lot = config.settings["lot_size"]
    risk_usd = config.settings["risk_dollars"]
    target_usd = config.settings["target_dollars"]
    pos_count = config.settings["position_count"] # New

    symbol = "XAUUSDm"
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if action == "BUY" else tick.bid

    # Calculate SL and TP once (so all positions have the same levels)
    points_sl = risk_usd / (lot * 100)
    points_tp = target_usd / (lot * 100)
    
    final_sl = round(price - points_sl if action == "BUY" else price + points_sl, 2)
    final_tp = round(price + points_tp if action == "BUY" else price - points_tp, 2)

    # --- THE LOOP: Open multiple positions ---
    for i in range(pos_count):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(lot),
            "type": mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": float(price),
            "sl": float(final_sl),
            "tp": float(final_tp),
            "magic": 123456, # This is why Close/BE works for all!
            "comment": f"Pos {i+1}/{pos_count}",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"🚀 Position {i+1} opened! Ticket: {result.ticket}")
        else:
            print(f"❌ Position {i+1} failed: {result.comment}")
    # 3. TAKE PROFIT LOGIC: Always use GUI Fixed Profit
    # We ignore the 'tp' variable from the signal entirely
    tp_points = target_usd / (lot * 100)
    final_tp = round(price + tp_points if action == "BUY" else price - tp_points, 2)
    print(f"🎯 Setting Fixed TP for ${target_usd} profit: {final_tp}")

    # 4. SEND TO MT5
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(lot),
        "type": mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL,
        "price": float(price),
        "sl": float(final_sl),
        "tp": float(final_tp),
        "magic": 123456,
        "comment": "GoldBot Polished",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Trade Failed: {result.comment}")
    else:
        print(f"🚀 {action} Opened! Ticket: {result.ticket}")

# (Keep your move_to_break_even and close_all_gold_trades functions as they are)

def move_to_break_even(symbol="XAUUSDm"):
    if not mt5.initialize():
        return

    # 1. Fetch all open positions for this symbol
    positions = mt5.positions_get(symbol=symbol)
    
    if not positions:
        print(f"No open positions found for {symbol} to move to BE.")
        return

    for pos in positions:
        # 2. Check Magic Number
        if pos.magic == 123456:
            # Entry Price is the new Stop Loss
            new_sl = pos.price_open
            
            # 3. Create the modification request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": pos.ticket,  # Required to identify which trade to change
                "sl": float(new_sl),     # Move SL to Entry Price
                "tp": float(pos.tp),     # Keep the original TP
                "magic": 123456
            }

            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"❌ BE Failed for #{pos.ticket}: {result.comment} (Error {result.retcode})")
            else:
                print(f"✅ BE Success! SL for #{pos.ticket} moved to {new_sl}")

def close_all_gold_trades(symbol="XAUUSDm"):
    if not mt5.initialize():
        print("MT5 Init Failed for Close")
        return

    # 1. Get all open positions
    positions = mt5.positions_get(symbol=symbol)
    
    if positions is None or len(positions) == 0:
        print(f"No open positions to close for {symbol}")
        return

    for pos in positions:
        # 2. Only close trades opened by our bot (Magic Number)
        if pos.magic == 123456:
            tick = mt5.symbol_info_tick(symbol)
            
            # To close a BUY (type 0), we must SELL. To close a SELL (type 1), we must BUY.
            type_close = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price_close = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": pos.ticket,       # CRITICAL: Must link to original ticket
                "symbol": symbol,
                "volume": pos.volume,         # Must match original volume
                "type": type_close,
                "price": price_close,
                "magic": 123456,
                "comment": "Bot Close Signal",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC, # Try ORDER_FILLING_FOK if this fails
            }
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"❌ Close Failed for #{pos.ticket}: {result.comment} (Error {result.retcode})")
            else:
                print(f"✅ Closed Ticket #{pos.ticket} at {result.price}")