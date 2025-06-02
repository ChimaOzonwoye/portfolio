import psutil
import subprocess
import time
import os
import sys
from functools import wraps
import ccxt

class StopLossManager:
    def __init__(self, risk_ratio=3.0):
        self.risk_ratio = risk_ratio
        self.active_stops = {}
        
    def calculate_dynamic_stop(self, entry_price, volatility):
        base_stop = entry_price * (1 - (volatility * 0.67))
        return max(base_stop, entry_price * 0.98)

    def update_profit_target(self, entry_price, stop_price):
        risk_amount = entry_price - stop_price
        return entry_price + (risk_amount * self.risk_ratio)

class SystemSafety:
    @staticmethod
    def maintain_connection():
        try:
            subprocess.check_call(['nmcli', 'networking', 'on'])
            subprocess.check_call(['systemctl', 'restart', 'network-manager'])
            time.sleep(5)
        except Exception as e:
            print(f"Connection recovery failed: {str(e)}")

    @staticmethod
    def resource_monitor(max_cpu=80, max_mem=85):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        return cpu <= max_cpu and mem <= max_mem

class ConnectionPreserver:
    def __init__(self, exchange):
        self.exchange = exchange
        self.max_retries = 5

    def secure_execute(self, func):  # Keep this indentation
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(self.max_retries):
                try:
                    if SystemSafety.resource_monitor():
                        return func(*args, **kwargs)
                    return None
                except (ccxt.NetworkError, ccxt.ExchangeError):
                    SystemSafety.maintain_connection()
                    time.sleep(2 ** attempt)
            print("Max retries reached, aborting trade")
            return None
        return wrapper
