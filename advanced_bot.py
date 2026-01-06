import os
import time
import json
import ccxt
import pandas as pd
import numpy as np
import talib
import logging
import threading
import requests
from datetime import datetime
from math import floor
from dotenv import load_dotenv

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('trading_bot_bitso.log'), logging.StreamHandler()]
)
logger = logging.getLogger("BitsoBot")

class RiskManager:
    def __init__(self, max_kelly=0.20):
        self.max_kelly = max_kelly
        self.trade_results = []

    def calculate_position_size(self, balance_mxn, current_price, atr):
        # Arriesgamos un % del capital basado en el ATR (volatilidad)
        risk_pct = 0.05 
        kelly_pct = max(0.01, min(risk_pct, self.max_kelly))
        
        amount_mxn = balance_mxn * kelly_pct
        return amount_mxn

class BitsoTradingBot:
    def __init__(self, config_path):
        load_dotenv()
        with open(config_path, 'r') as f:
            self.config = json.load(f)
            
        # Conexión a Bitso
        self.exchange = ccxt.bitso({
            'apiKey': os.getenv('BITSO_API_KEY'),
            'secret': os.getenv('BITSO_API_SECRET'),
            'enableRateLimit': True
        })
        
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.symbol = self.config.get('symbol', 'BTC/MXN')
        self.timeframe = self.config.get('timeframe', '5m')
        self.active_position = None
        self.is_running = True
        
        # Iniciar monitoreo
        self.send_telegram(f"🇲🇽 Bot Bitso activado: Operando {self.symbol}")

    def send_telegram(self, message):
        if not self.telegram_token: return
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            requests.post(url, json={"chat_id": self.telegram_chat_id, "text": message}, timeout=5)
        except Exception as e: logger.error(f"Error Telegram: {e}")

    def get_precision_amount(self, amount):
        # Bitso es muy estricto con los decimales
        market = self.exchange.market(self.symbol)
        precision = market['precision']['amount']
        return floor(amount * (10**precision)) / (10**precision)

    def run_cycle(self):
        logger.info(f"--- Consultando Bitso ({self.symbol}) ---")
        try:
            # 1. Obtener Velas (OHLCV)
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe=self.timeframe, limit=50)
            df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
            
            # 2. Calcular Indicadores
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            
            current_price = df['close'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            current_atr = df['atr'].iloc[-1]

            print(f"📊 Precio {self.symbol}: ${current_price} MXN | RSI: {current_rsi:.2f}")

            # 3. Lógica de Compra (Si no tenemos posición)
            if not self.active_position:
                if current_rsi < 35: # Sobrevendido (Barato)
                    balance = self.exchange.fetch_balance()
                    mxn_disponible = balance['free'].get('MXN', 0)
                    
                    # Usar 10% del balance por operación para pruebas
                    monto_compra_mxn = mxn_disponible * 0.10
                    
                    if monto_compra_mxn > 100: # Mínimo sugerido en Bitso para evitar errores
                        cantidad_crypto = self.get_precision_amount(monto_compra_mxn / current_price)
                        
                        logger.info(f"🛒 Comprando {cantidad_crypto} {self.symbol}")
                        order = self.exchange.create_market_buy_order(self.symbol, cantidad_crypto)
                        
                        self.active_position = {
                            'amount': cantidad_crypto,
                            'buy_price': current_price,
                            'stop_loss': current_price - (current_atr * 2),
                            'take_profit': current_price + (current_atr * 3)
                        }
                        self.send_telegram(f"📦 COMPRA ejecutada en {self.symbol}\nPrecio: ${current_price} MXN")
                else:
                    print(f"⏳ Buscando entrada... RSI actual {current_rsi:.2f}")

            # 4. Lógica de Venta (Si ya compramos)
            else:
                sl = self.active_position['stop_loss']
                tp = self.active_position['take_profit']
                
                if current_price <= sl or current_price >= tp or current_rsi > 70:
                    razon = "Take Profit" if current_price >= tp else "Stop Loss" if current_price <= sl else "RSI Alto"
                    
                    logger.info(f"🚀 Vendiendo por {razon}")
                    self.exchange.create_market_sell_order(self.symbol, self.active_position['amount'])
                    
                    ganancia = (current_price - self.active_position['buy_price'])
                    self.send_telegram(f"💰 VENTA por {razon}\nGanancia/Pérdida: ${ganancia:.2f} MXN")
                    self.active_position = None

        except Exception as e:
            logger.error(f"Error en ciclo Bitso: {e}")

if __name__ == "__main__":
    # Asegúrate de que config_advanced.json tenga "symbol": "BTC/MXN"
    bot = BitsoTradingBot('config_advanced.json')
    while True:
        bot.run_cycle()
        time.sleep(60) # Revisar cada minuto