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
def place_gold_trade(action, entry, sl, tp):
    if not mt5.initialize():
        print("❌ MT5 Initialization failed")
        return

    # --- NEW: FETCH SETTINGS FROM GUI ---
    current_lot = config.settings["lot_size"]
    current_risk_dollars = config.settings["risk_dollars"]

    symbol = "XAUUSDm"
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    
    if tick is None:
        print(f"❌ Could not get price for {symbol}")
        return

    price = tick.ask if action == "BUY" else tick.bid
    
    # --- UPDATED SAFETY SL ---
    if sl is None or str(sl).strip() == "":
        # We now use 'current_risk_dollars' and 'current_lot' from GUI
        final_sl = calculate_safety_sl(action, price, current_risk_dollars, current_lot)
        print(f"⚠️ No SL in signal. GUI Safety SL: {final_sl} (Risk: ${current_risk_dollars})")
    else:
        final_sl = round(float(sl), 2)

    # --- DEFAULT TP (1:2 Ratio) ---
    if tp is None or str(tp).strip() == "":
        dist = abs(price - final_sl)
        final_tp = round(price + (dist * 2) if action == "BUY" else price - (dist * 2), 2)
        print(f"⚠️ No TP in signal. Calculated TP: {final_tp}")
    else:
        final_tp = round(float(tp), 2)

    # Build Request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(current_lot), # Uses the value from GUI dropdown
        "type": mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL,
        "price": float(price),
        "sl": float(final_sl),
        "tp": float(final_tp),
        "magic": 123456,
        "comment": "Gold Bot V2",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    print(f"📡 Sending Order: {action} {symbol} | Lot: {current_lot} | SL: {final_sl}")
    
    result = mt5.order_send(request)
    
    if result is None:
        print("❌ MT5 Error: No response from server")
    elif result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Trade Failed! Error {result.retcode}: {result.comment}")
    else:
        print(f"✅ SUCCESS: {action} opened at {result.price}")

# move_to_break_even and close_all_gold_trades remain exactly as you have them!
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