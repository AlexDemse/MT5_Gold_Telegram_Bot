import os
import re
import asyncio
from telethon import TelegramClient, events
from dotenv import load_dotenv
from trading import place_gold_trade
from trading import move_to_break_even

load_dotenv()

# --- CONFIGURATION ---
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
# PASTE YOUR LINK HERE (e.g., 'https://t.me/YourSignalChannel' or '+AbC123...')
CHANNEL_LINK = "https://t.me/k100million" 

client = TelegramClient('gold_session', API_ID, API_HASH)

# Global variable to store the ID once we find it
target_id = 1003315419486

@client.on(events.NewMessage)
async def my_event_handler(event):
    global target_id
    
    # ID Normalization
    incoming = str(event.chat_id).replace("-100", "").replace("-", "")
    target = str(target_id).replace("-100", "").replace("-", "")

    if incoming != target:
        return 

    msg = event.raw_text.upper()
    print(f"✅ Verified Signal Received: {msg}")

    # --- CLOSE SIGNAL LOGIC ---
    # We check if any of these trigger words are in the message
    close_triggers = ["CLOSE", "CLOSS", "EXIT", "CLOSE ALL"]
    
    if any(trigger in msg for trigger in close_triggers):
        print("🛑 Close command detected!")
        from trading import close_all_gold_trades
        close_all_gold_trades("XAUUSDm")
        return # Stop processing further so it doesn't try to open a new trade
    # --- BREAK EVEN SIGNAL LOGIC ---
    be_triggers = ["MOVE SL TO BE", "SL TO ENTRY", "SL TO BE", "BREAKEVEN", "BREAK EVEN"]
    
    if any(trigger in msg for trigger in be_triggers):
        print("⚡ Break Even command detected!")
        from trading import move_to_break_even
        move_to_break_even("XAUUSDm")
        return  # Stop here
    

    action = "BUY" if "BUY" in msg else "SELL" if "SELL" in msg else None
    
    if action and ("GOLD" in msg or "XAUUSD" in msg):
        # Extract all numbers
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", msg)
        
        # Default them to None so trading.py knows to calculate them
        sl = None
        tp = None

        if "NOW" in msg or len(numbers) == 0:
            # Format: "SELL GOLD NOW SL 2150" -> numbers[0] is SL
            if len(numbers) >= 1: sl = numbers[0]
            if len(numbers) >= 2: tp = numbers[1]
        else:
            # Format: "BUY GOLD 2150 SL 2140 TP 2170"
            if len(numbers) >= 2: sl = numbers[1]
            if len(numbers) >= 3: tp = numbers[2]

        # Call the trade function
        place_gold_trade(action, 0, sl, tp)

async def main():
    global target_id
    print("--- Connecting to Telegram ---")
    await client.start()
    
    # Convert the link into a real ID
    try:
        entity = await client.get_entity(CHANNEL_LINK)
        target_id = entity.id
        print(f"🎯 Locked onto Channel: {entity.title} (ID: {target_id})")
    except Exception as e:
        print(f"❌ Error finding channel link: {e}")
        return

    print("--- Bot is LIVE and Listening ---")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
