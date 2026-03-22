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
    
    # 1. ID Normalization
    incoming = str(event.chat_id).replace("-100", "").replace("-", "")
    target = str(target_id).replace("-100", "").replace("-", "")

    if incoming != target:
        return 

    msg = event.raw_text.upper()
    print(f"✅ Verified Signal Received: {msg}")

    # 2. CLOSE SIGNAL LOGIC
    close_triggers = ["CLOSE", "CLOSS", "EXIT", "CLOSE ALL"]
    if any(trigger in msg for trigger in close_triggers):
        print("🛑 Close command detected!")
        from trading import close_all_gold_trades
        close_all_gold_trades("XAUUSDm")
        return 

    # 3. BREAK EVEN SIGNAL LOGIC
    be_triggers = ["MOVE SL TO BE", "SL TO ENTRY", "SL TO BE", "BREAKEVEN", "BREAK EVEN", "SL BE"]
    if any(trigger in msg for trigger in be_triggers):
        print("⚡ Break Even command detected!")
        from trading import move_to_break_even
        move_to_break_even("XAUUSDm")
        return 

    # 4. NEW TRADE LOGIC (Simplified for GUI Fixed TP)
    action = "BUY" if "BUY" in msg else "SELL" if "SELL" in msg else None
    
    if action and ("GOLD" in msg or "XAUUSD" in msg):
        # Extract numbers - we only need to look for a potential SL
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", msg)
        
        sl = None
        
        # LOGIC: Grab the number that follows 'SL' if it exists. 
        # If no 'SL' word, we take the 1st number as SL (for 'BUY NOW 2500' type signals)
        if "SL" in msg and len(numbers) >= 1:
            # Usually SL is the first number after the word 'SL'
            sl = numbers[0] 
        elif len(numbers) >= 1:
            sl = numbers[0]

        # Call the trade function. 
        # Entry=0 (we use market price) and TP=None (trading.py uses GUI settings)
        print(f"📡 Sending {action} Signal to Executor...")
        place_gold_trade(action, 0, sl, None)
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
