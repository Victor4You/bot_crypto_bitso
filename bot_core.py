# bot_core.py
import ccxt
import pandas as pd
import numpy as np
import talib
from datetime import datetime
import time
import logging
from typing import Dict, List, Optional
import json

class TradingBot:
    def __init__(self, exchange_id: str = 'binance'):
        """
        Inicializa el bot de trading
        """
        self.exchange_id = exchange_id
        self.exchange = self._initialize_exchange()
        self.symbol = 'BTC/USDT'
        self.timeframe = '1h'
        self.balance = {}
        self.positions = {}
        self.is_running = False
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _initialize_exchange(self):
        """Configura la conexión con el exchange"""
        exchange_class = getattr(ccxt, self.exchange_id)
        exchange = exchange_class({
            'apiKey': 'TU_API_KEY',  # Usar variables de entorno en producción
            'secret': 'TU_API_SECRET',
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # Verificar conectividad
        try:
            exchange.load_markets()
            self.logger.info(f"Conectado a {self.exchange_id.upper()}")
            return exchange
        except Exception as e:
            self.logger.error(f"Error conectando: {e}")
            raise
    
    def fetch_ohlcv(self, limit: int = 100):
        """Obtiene datos OHLCV (Open, High, Low, Close, Volume)"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol,
                timeframe=self.timeframe,
                limit=limit
            )
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV: {e}")
            return None
    
    def calculate_indicators(self, df: pd.DataFrame):
        """Calcula indicadores técnicos"""
        df = df.copy()
        
        # Media móvil simple
        df['sma_20'] = talib.SMA(df['close'], timeperiod=20)
        df['sma_50'] = talib.SMA(df['close'], timeperiod=50)
        
        # RSI
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
            df['close'],
            fastperiod=12,
            slowperiod=26,
            signalperiod=9
        )
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'],
            timeperiod=20,
            nbdevup=2,
            nbdevdn=2
        )
        
        # Volumen promedio
        df['volume_sma'] = talib.SMA(df['volume'], timeperiod=20)
        
        return df
    
    def generate_signals(self, df: pd.DataFrame):
        """Genera señales de compra/venta basadas en indicadores"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        signals = {
            'buy': False,
            'sell': False,
            'strength': 0,
            'reasons': []
        }
        
        # Estrategia: Cruce de medias móviles + RSI
        if latest['sma_20'] > latest['sma_50'] and prev['sma_20'] <= prev['sma_50']:
            if latest['rsi'] < 70:  # No sobrecomprado
                signals['buy'] = True
                signals['strength'] += 1
                signals['reasons'].append('Cruce alcista de medias')
        
        if latest['sma_20'] < latest['sma_50'] and prev['sma_20'] >= prev['sma_50']:
            if latest['rsi'] > 30:  # No sobrevendido
                signals['sell'] = True
                signals['strength'] += 1
                signals['reasons'].append('Cruce bajista de medias')
        
        # Confirmación con MACD
        if latest['macd'] > latest['macd_signal']:
            signals['strength'] += 0.5
            signals['reasons'].append('MACD positivo')
        
        # Bollinger Bands
        if latest['close'] < latest['bb_lower']:
            signals['buy'] = True
            signals['strength'] += 0.8
            signals['reasons'].append('Precio en banda inferior BB')
        
        return signals
    
    def execute_order(self, side: str, amount: float, order_type: str = 'market'):
        """Ejecuta una orden en el exchange"""
        try:
            order = self.exchange.create_order(
                symbol=self.symbol,
                type=order_type,
                side=side,
                amount=amount
            )
            self.logger.info(f"Orden {side} ejecutada: {order['id']}")
            return order
        except Exception as e:
            self.logger.error(f"Error ejecutando orden: {e}")
            return None
    
    def risk_management(self, df: pd.DataFrame):
        """Gestión de riesgo - Calcula stop loss y take profit"""
        latest = df.iloc[-1]
        atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14).iloc[-1]
        
        # Stop loss dinámico basado en ATR
        stop_loss_pct = atr / latest['close'] * 3  # 3x ATR
        
        risk_params = {
            'stop_loss': 0.02,  # 2% mínimo
            'take_profit': 0.04,  # 4%
            'position_size': 0.1,  # 10% del capital por trade
            'max_drawdown': 0.15  # Máxima pérdida permitida
        }
        
        # Ajustar stop loss basado en volatilidad
        risk_params['stop_loss'] = max(risk_params['stop_loss'], stop_loss_pct)
        
        return risk_params
    
    def run(self):
        """Bucle principal del bot"""
        self.is_running = True
        self.logger.info("Iniciando bot de trading...")
        
        while self.is_running:
            try:
                # 1. Obtener datos del mercado
                df = self.fetch_ohlcv(limit=100)
                if df is None:
                    time.sleep(60)
                    continue
                
                # 2. Calcular indicadores
                df = self.calculate_indicators(df)
                
                # 3. Generar señales
                signals = self.generate_signals(df)
                
                # 4. Gestión de riesgo
                risk = self.risk_management(df)
                
                # 5. Ejecutar lógica de trading
                if signals['buy'] and signals['strength'] > 1:
                    self.logger.info(f"Señal COMPRA: {signals['reasons']}")
                    # Aquí implementar lógica de ejecución real
                
                elif signals['sell'] and signals['strength'] > 1:
                    self.logger.info(f"Señal VENTA: {signals['reasons']}")
                    # Aquí implementar lógica de ejecución real
                
                # 6. Esperar para siguiente iteración
                time.sleep(300)  # 5 minutos entre checks
                
            except KeyboardInterrupt:
                self.logger.info("Bot detenido por usuario")
                self.is_running = False
            except Exception as e:
                self.logger.error(f"Error en bucle principal: {e}")
                time.sleep(60)