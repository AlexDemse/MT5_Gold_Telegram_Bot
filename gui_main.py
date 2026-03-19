import customtkinter as ctk
import threading
import asyncio
import config # Import our new shared settings
from main import main as start_telegram

class GoldBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gold Bot Control Panel")
        self.geometry("400x550")

        # --- SETTINGS SECTION ---
        ctk.CTkLabel(self, text="⚙️ TRADE SETTINGS", font=("Arial", 16, "bold")).pack(pady=10)

        # Lot Size Dropdown
        ctk.CTkLabel(self, text="Select Lot Size:").pack()
        self.lot_dropdown = ctk.CTkOptionMenu(self, values=["0.01", "0.02", "0.05", "0.10", "0.50"], command=self.update_lot)
        self.lot_dropdown.set("0.01")
        self.lot_dropdown.pack(pady=5)

        # Risk Dollar Entry
        ctk.CTkLabel(self, text="Default Risk (USD $):").pack()
        self.risk_entry = ctk.CTkEntry(self, placeholder_text="15.0")
        self.risk_entry.insert(0, "15.0")
        self.risk_entry.pack(pady=5)
        
        # Save Settings Button
        self.save_btn = ctk.CTkButton(self, text="APPLY SETTINGS", fg_color="blue", command=self.apply_settings)
        self.save_btn.pack(pady=10)

        # --- LOG & CONTROLS ---
        self.log_box = ctk.CTkTextbox(self, width=350, height=150)
        self.log_box.pack(pady=10)

        self.start_btn = ctk.CTkButton(self, text="START BOT", fg_color="green", command=self.run_bot_thread)
        self.start_btn.pack(pady=5)

    def update_lot(self, choice):
        config.settings["lot_size"] = float(choice)
        self.log_box.insert("end", f"System: Lot Size set to {choice}\n")

    def apply_settings(self):
        try:
            risk = float(self.risk_entry.get())
            config.settings["risk_dollars"] = risk
            self.log_box.insert("end", f"✅ Applied: Risking ${risk} per trade\n")
        except ValueError:
            self.log_box.insert("end", "❌ Error: Risk must be a number!\n")

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