import numpy as np
import json
import os
import logging
from collections import deque

class RiskManager:
    def __init__(self, config_path='config_advanced.json'):
        # Cargar configuración
        with open(config_path, 'r') as f:
            config = json.load(f)['risk_management']
            
        self.max_drawdown = config.get('max_drawdown', 0.15)
        self.max_position_size_pct = config.get('max_position_size', 0.1)
        self.max_kelly = config.get('max_kelly', 0.25) # Límite de seguridad para Kelly
        
        # Historial de trades (Persistencia)
        self.history_file = 'data/trade_history.json'
        self.trade_results = self._load_history() # Lista de % de retorno de cada trade
        
        self.logger = logging.getLogger("RiskManager")

    def _load_history(self):
        """Carga los resultados de trades previos para calcular el Kelly real"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return []

    def update_history(self, pnl_pct):
        """Registra el resultado de un trade y lo guarda"""
        self.trade_results.append(pnl_pct)
        # Mantener solo los últimos 50 trades para adaptabilidad
        if len(self.trade_results) > 50:
            self.trade_results.pop(0)
            
        with open(self.history_file, 'w') as f:
            json.dump(self.trade_results, f)

    def calculate_dynamic_kelly(self):
        """Calcula el Criterio de Kelly basado en el rendimiento real del bot"""
        if len(self.trade_results) < 5: # Mínimo de trades para empezar a calcular
            return self.max_position_size_pct / 2 # Empezar conservador

        wins = [r for r in self.trade_results if r > 0]
        losses = [r for r in self.trade_results if r <= 0]
        
        win_rate = len(wins) / len(self.trade_results)
        avg_win = np.mean(wins) if wins else 0.01
        avg_loss = abs(np.mean(losses)) if losses else 0.01
        
        # Fórmula de Kelly: K% = W - [(1 - W) / (AvgWin / AvgLoss)]
        ratio = avg_win / avg_loss
        kelly = win_rate - ((1 - win_rate) / ratio)
        
        # Aplicamos "Fractional Kelly" (usar solo el 25% del Kelly sugerido por seguridad)
        safe_kelly = kelly * 0.25
        
        # Limitar por la configuración máxima
        return max(0.01, min(safe_kelly, self.max_kelly))

    def get_position_size(self, balance, current_price, atr):
        """
        Calcula el tamaño de la posición basado en volatilidad (ATR)
        Si el mercado está muy volátil, el tamaño de la posición baja.
        """
        kelly_pct = self.calculate_dynamic_kelly()
        
        # Riesgo por trade basado en ATR (ej: arriesgar el Kelly_pct si el precio se mueve 2 ATRs)
        stop_loss_dist = atr * 2
        risk_per_share = stop_loss_dist
        
        if risk_per_share == 0: return 0
        
        # Cantidad de capital a arriesgar
        capital_at_risk = balance * kelly_pct
        
        # Tamaño de la posición en unidades del activo
        position_size_units = capital_at_risk / risk_per_share
        
        # Convertir a valor nominal (USDT)
        position_value_usdt = position_size_units * current_price
        
        self.logger.info(f"Kelly Sugerido: {kelly_pct:.2%}, Valor Posición: {position_value_usdt:.2f} USDT")
        
        return position_value_usdt