import os
import re
from telethon import TelegramClient, events
from dotenv import load_dotenv
from trading import place_gold_trade

load_dotenv()

# Setup Telegram Connection
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
client = TelegramClient('gold_session', API_ID, API_HASH)

print("--- Gold Trading Bot Starting... Listening for Signals ---")

@client.on(events.NewMessage)
async def my_event_handler(event):
    msg = event.raw_text.upper()

    # KEYWORD ACTIVATION: Only trigger if Gold and Buy/Sell are mentioned
    if ("GOLD" in msg or "XAUUSD" in msg) and ("BUY" in msg or "SELL" in msg):
        print(f"New Signal Detected: {msg}")

        # Find all numbers (prices) in the message
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", msg)

        if len(numbers) >= 3:
            action = "BUY" if "BUY" in msg else "SELL"
            # Assumptions based on common signal formats:
            # Entry = 1st number, SL = 2nd number, TP = 3rd number
            entry_price = numbers[0]
            stop_loss = numbers[1]
            take_profit = numbers[2]

            print(f"Processing: {action} | Entry: {entry_price} | SL: {stop_loss} | TP: {take_profit}")
            
            # Execute the trade
            place_gold_trade(action, entry_price, stop_loss, take_profit)
        else:
            print("Signal found, but not enough price data (SL/TP) detected.")

with client:
    client.run_until_disconnected()