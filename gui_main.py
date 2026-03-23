import customtkinter as ctk
import threading
import asyncio
import config 
from main import main as start_telegram
import MetaTrader5 as mt5

class GoldBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gold Bot Control Panel")
        self.geometry("400x800") 

        # --- 1. LIVE STATS HUD ---
        self.stats_frame = ctk.CTkFrame(self, fg_color="#2B2B2B", border_width=2, border_color="blue")
        self.stats_frame.pack(pady=10, fill="x", padx=20)

        self.equity_label = ctk.CTkLabel(self.stats_frame, text="Equity: $0.00", font=("Arial", 14))
        self.equity_label.pack(pady=2)

        self.profit_label = ctk.CTkLabel(self.stats_frame, text="Open P/L: $0.00", font=("Arial", 18, "bold"))
        self.profit_label.pack(pady=5)

        # THE NEW CLOSE ALL BUTTON (Inside HUD)
        self.close_all_btn = ctk.CTkButton(
            self.stats_frame, 
            text="🔴 CLOSE ALL TRADES", 
            fg_color="#c0392b", 
            hover_color="#e74c3c",
            command=self.manual_close_all
        )
        self.close_all_btn.pack(pady=10, padx=20)

        # --- 2. SETTINGS SECTION ---
        ctk.CTkLabel(self, text="⚙️ TRADE SETTINGS", font=("Arial", 16, "bold")).pack(pady=5)
        
        self.lot_dropdown = ctk.CTkOptionMenu(self, values=["0.01", "0.02", "0.05", "0.10", "0.50"], command=self.update_lot)
        self.lot_dropdown.set("0.01")
        self.lot_dropdown.pack(pady=2)

        self.create_setting_field("Risk (USD $):", "risk_entry", "15.0")
        self.create_setting_field("Target (USD $):", "tp_entry", "30.0")
        self.create_setting_field("Positions:", "count_entry", "1")
        self.create_setting_field("Auto BE after (Pips):", "be_pips_entry", "150")

        self.save_btn = ctk.CTkButton(self, text="APPLY SETTINGS", fg_color="blue", command=self.apply_settings)
        self.save_btn.pack(pady=10)

        # --- 3. LOG & CONTROLS ---
        self.log_box = ctk.CTkTextbox(self, width=350, height=150)
        self.log_box.pack(pady=5)

        self.start_btn = ctk.CTkButton(self, text="START BOT", fg_color="green", command=self.run_bot_thread)
        self.start_btn.pack(pady=5)

        self.update_live_stats()

    def manual_close_all(self):
        """Emergency button to close all bot-opened trades"""
        if not mt5.initialize(): return
        
        positions = mt5.positions_get(group="*XAUUSD*")
        if not positions:
            self.write_log("ℹ️ No open Gold trades to close.")
            return

        count = 0
        for pos in positions:
            if pos.magic == 123456:
                # Close Logic
                tick = mt5.symbol_info_tick(pos.symbol)
                type_close = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                price_close = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "position": pos.ticket,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": type_close,
                    "price": price_close,
                    "magic": 123456,
                    "comment": "Manual GUI Close",
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                mt5.order_send(request)
                count += 1
        
        self.write_log(f"🔴 Manual Close: {count} trades exited.")

    # ... (Keep your existing helper functions like update_live_stats, execute_be, etc.)

    def create_setting_field(self, label_text, attr_name, default_val):
        ctk.CTkLabel(self, text=label_text).pack()
        entry = ctk.CTkEntry(self, width=100)
        entry.insert(0, default_val)
        entry.pack(pady=2)
        setattr(self, attr_name, entry)

    def update_live_stats(self):
        if not mt5.initialize():
            self.equity_label.configure(text="MT5: Not Connected")
        else:
            acc = mt5.account_info()
            if acc:
                self.equity_label.configure(text=f"Equity: ${acc.equity:,.2f}")
                
                # Use the 'active_be_pips' we saved when Apply was clicked
                # We use getattr in case the bot starts before 'Apply' is clicked the first time
                current_be_target = getattr(self, 'active_be_pips', 150.0) 

                positions = mt5.positions_get(group="*XAUUSD*")
                bot_profit = 0.0
                
                if positions:
                    for pos in positions:
                        if pos.magic == 123456:
                            bot_profit += (pos.profit + pos.swap + getattr(pos, 'commission', 0.0))

                            # PIP CALCULATION
                            if pos.type == mt5.ORDER_TYPE_BUY:
                                pips_away = (pos.price_current - pos.price_open) * 10
                                target_be_sl = pos.price_open + 0.2
                                # Only move if pips >= our STABLE target
                                if pips_away >= current_be_target and pos.sl < target_be_sl:
                                    self.execute_be(pos, target_be_sl)
                            else: # SELL
                                pips_away = (pos.price_open - pos.price_current) * 10
                                target_be_sl = pos.price_open - 0.2
                                if pips_away >= current_be_target and (pos.sl > target_be_sl or pos.sl == 0):
                                    self.execute_be(pos, target_be_sl)

                p_color = "#2ecc71" if bot_profit >= 0 else "#e74c3c"
                self.profit_label.configure(text=f"Open P/L: ${bot_profit:.2f}", text_color=p_color)

        self.after(1000, self.update_live_stats)

    def execute_be(self, pos, new_sl):
        request = {"action": mt5.TRADE_ACTION_SLTP, "position": pos.ticket, "sl": round(new_sl, 2), "tp": pos.tp}
        mt5.order_send(request)
        self.write_log(f"🛡️ Ticket #{pos.ticket} moved to BE!")

    def write_log(self, text):
        self.log_box.insert("end", f"> {text}\n")
        self.log_box.see("end")

    def update_lot(self, choice):
        config.settings["lot_size"] = float(choice)

    def apply_settings(self):
        try:
            # 1. Update the shared config/hidden variables
            config.settings["risk_dollars"] = float(self.risk_entry.get())
            config.settings["target_dollars"] = float(self.tp_entry.get())
            config.settings["position_count"] = int(self.count_entry.get())
            
            # 2. NEW: Save the BE Pips to a dedicated variable so the watcher stays stable
            self.active_be_pips = float(self.be_pips_entry.get())
            
            self.write_log(f"✅ Settings Applied! (BE Target: {self.active_be_pips} pips)")
        except ValueError:
            self.write_log("❌ Error: Use numbers only in settings!")

    def run_bot_thread(self):
        self.start_btn.configure(state="disabled", text="RUNNING")
        threading.Thread(target=self.start_async, daemon=True).start()

    def start_async(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_telegram())

if __name__ == "__main__":
    app = GoldBotGUI()
    app.mainloop()