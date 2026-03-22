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
CHANNEL_LINK = "https://t.me/+0UEudMz-wcczOWQ1" 

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

   # 4. NEW TRADE LOGIC (Final Polish for "NOW" vs "SL")
    
    # --- A. THE GATEKEEPER (Ignore "LOOKING", "WATCHING", etc.) ---
    ignore_triggers = ["LOOKING", "WATCHING", "WAITING", "POTENTIAL", "PREPARE"]
    if any(word in msg for word in ignore_triggers):
        print(f"👀 Info: Ignoring opinion message: {msg}")
        return

    # --- B. DETECT ACTION ---
    action = "BUY" if "BUY" in msg else "SELL" if "SELL" in msg else None
    
    if action and ("GOLD" in msg or "XAUUSD" in msg):
        sl = None
        
        # --- C. SMART SL EXTRACTION (Only if 'SL' keyword exists) ---
        if "SL" in msg:
            # We split at "SL" and grab the number immediately following it
            try:
                parts = msg.split("SL")
                # Look for numbers only in the part AFTER the word "SL"
                sl_numbers = re.findall(r"[-+]?\d*\.\d+|\d+", parts[1])
                if sl_numbers:
                    sl = sl_numbers[0]
                    print(f"🛡️ Valid SL found after keyword: {sl}")
            except Exception as e:
                print(f"⚠️ Error parsing SL: {e}")
        
        # --- D. THE "NOW" RULE ---
        # If no "SL" keyword was found, we send 'None' to trading.py
        # This prevents the bot from accidentally using the Entry Price as an SL
        if sl is None:
            print(f"⚠️ No explicit SL found. Using GUI Default Risk.")

        # --- E. EXECUTION ---
        # Entry=0 (Market Price), TP=None (GUI Ladder settings)
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
