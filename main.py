import os
import re
import asyncio # Add this import at the top!
from telethon import TelegramClient, events
from dotenv import load_dotenv
from trading import place_gold_trade

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')

# 1. Create the client
client = TelegramClient('gold_session', API_ID, API_HASH)

@client.on(events.NewMessage)
async def my_event_handler(event):
    msg = event.raw_text.upper()
    if ("GOLD" in msg or "XAUUSD" in msg) and ("BUY" in msg or "SELL" in msg):
        print(f"New Signal Detected: {msg}")
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", msg)
        if len(numbers) >= 3:
            action = "BUY" if "BUY" in msg else "SELL"
            entry_price, stop_loss, take_profit = numbers[0], numbers[1], numbers[2]
            print(f"Executing: {action} | SL: {stop_loss} | TP: {take_profit}")
            place_gold_trade(action, entry_price, stop_loss, take_profit)

# 2. Modern way to start the bot to avoid the "Event Loop" error
async def main():
    print("--- Gold Trading Bot Starting... Listening for Signals ---")
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")