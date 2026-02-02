import os
import time
import json
import ccxt
import pandas as pd
import numpy as np
import logging
import requests
from datetime import datetime, time as dt_time
import pytz 
from math import floor
from dotenv import load_dotenv

# 1. Configuración de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('trading_bot_bitso.log'), logging.StreamHandler()]
)
logger = logging.getLogger("BitsoHybridBot")

class BitsoTradingBot:
    def __init__(self, config_path):
        load_dotenv()
        with open(config_path, 'r') as f:
            self.config = json.load(f)
            
        self.exchange = ccxt.bitso({
            'apiKey': os.getenv('BITSO_API_KEY'),
            'secret': os.getenv('BITSO_API_SECRET'),
            'enableRateLimit': True
        })
        
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.symbols = self.config.get('symbols', ['BTC/MXN', 'NVDA/MXN', 'AAPL/MXN'])
        self.timeframe = self.config.get('timeframe', '5m')
        self.active_positions = {} 
        self.send_telegram("🚀 Bot Bitso Online (Cripto + Acciones).")

    def calculate_rsi(self, series, period=14):
        """Calcula el RSI manualmente sin librerías externas."""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_atr(self, df, period=14):
        """Calcula el ATR manualmente."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()

    def is_market_open(self, symbol):
        criptos = ['BTC', 'ETH', 'XRP', 'SOL', 'LTC', 'USD']
        if any(c in symbol.upper() for c in criptos): return True
        tz_ny = pytz.timezone('America/New_York')
        now_ny = datetime.now(tz_ny)
        if now_ny.weekday() >= 5: return False
        return dt_time(9, 30) <= now_ny.time() <= dt_time(16, 0)

    def send_telegram(self, message):
        if not self.telegram_token: return
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            requests.post(url, json={"chat_id": self.telegram_chat_id, "text": message}, timeout=5)
        except Exception as e: logger.error(f"Error Telegram: {e}")

    def get_precision_amount(self, symbol, amount):
        market = self.exchange.market(symbol)
        precision = market['precision']['amount']
        return floor(amount * (10**precision)) / (10**precision)

    def run_cycle(self):
        for symbol in self.symbols:
            if not self.is_market_open(symbol): continue
            logger.info(f"--- Analizando {symbol} ---")
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=self.timeframe, limit=100)
                df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
                
                # Cálculo manual de indicadores
                df['rsi'] = self.calculate_rsi(df['close'])
                df['atr'] = self.calculate_atr(df)
                
                if pd.isna(df['rsi'].iloc[-1]): continue

                current_price = df['close'].iloc[-1]
                current_rsi = df['rsi'].iloc[-1]
                current_atr = df['atr'].iloc[-1]

                print(f"📊 {symbol}: ${current_price} | RSI: {current_rsi:.2f}")

                if symbol not in self.active_positions:
                    if current_rsi < 35:
                        balance = self.exchange.fetch_balance()
                        mxn_disponible = balance['free'].get('MXN', 0)
                        if mxn_disponible > 200:
                            cantidad = self.get_precision_amount(symbol, 200 / current_price)
                            self.exchange.create_market_buy_order(symbol, cantidad)
                            self.active_positions[symbol] = {
                                'amount': cantidad, 'buy_price': current_price,
                                'stop_loss': current_price - (current_atr * 2),
                                'take_profit': current_price + (current_atr * 3)
                            }
                            self.send_telegram(f"✅ COMPRA: {symbol} a ${current_price}")
                else:
                    pos = self.active_positions[symbol]
                    if current_price <= pos['stop_loss'] or current_price >= pos['take_profit'] or current_rsi > 70:
                        self.exchange.create_market_sell_order(symbol, pos['amount'])
                        pnl = (current_price - pos['buy_price']) * pos['amount']
                        self.send_telegram(f"💰 VENTA: {symbol}\nResultado: ${pnl:.2f} MXN")
                        del self.active_positions[symbol]
            except Exception as e:
                logger.error(f"Error en {symbol}: {e}")

if __name__ == "__main__":
    bot = BitsoTradingBot('config_advanced.json')
    while True:
        bot.run_cycle()
        time.sleep(60)