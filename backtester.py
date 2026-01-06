# backtester.py
import backtrader as bt
import backtrader.analyzers as btanalyzers
import pandas as pd

class MovingAverageCrossStrategy(bt.Strategy):
    params = (
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
    )
    
    def __init__(self):
        # Indicadores
        self.sma_short = bt.indicators.SMA(
            self.data.close, 
            period=self.params.sma_short
        )
        self.sma_long = bt.indicators.SMA(
            self.data.close, 
            period=self.params.sma_long
        )
        self.rsi = bt.indicators.RSI(
            self.data.close,
            period=self.params.rsi_period
        )
        
        # Variables de seguimiento
        self.order = None
        self.buy_price = None
        
    def next(self):
        # Si hay una orden pendiente, no hacer nada
        if self.order:
            return
        
        # Condición de compra: SMA corta cruza por encima de larga y RSI no sobrecomprado
        buy_condition = (
            self.sma_short[0] > self.sma_long[0] and
            self.sma_short[-1] <= self.sma_long[-1] and
            self.rsi[0] < self.params.rsi_overbought
        )
        
        # Condición de venta: SMA corta cruza por debajo de larga y RSI no sobrevendido
        sell_condition = (
            self.sma_short[0] < self.sma_long[0] and
            self.sma_short[-1] >= self.sma_long[-1] and
            self.rsi[0] > self.params.rsi_oversold
        )
        
        # Lógica de trading
        if not self.position and buy_condition:
            # Calcular tamaño de posición (10% del capital)
            size = self.broker.getcash() * 0.1 / self.data.close[0]
            self.order = self.buy(size=size)
            
        elif self.position and sell_condition:
            self.order = self.sell(size=self.position.size)

def run_backtest(data_path, initial_cash=10000):
    """Ejecuta backtesting completo"""
    
    # Crear cerebro de backtrader
    cerebro = bt.Cerebro()
    
    # Agregar estrategia
    cerebro.addstrategy(MovingAverageCrossStrategy)
    
    # Cargar datos
    data = bt.feeds.GenericCSVData(
        dataname=data_path,
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1,
        dtformat=('%Y-%m-%d %H:%M:%S'),
        timeframe=bt.TimeFrame.Minutes,
        compression=60
    )
    cerebro.adddata(data)
    
    # Configurar broker
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% comisión
    
    # Agregar analizadores
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(btanalyzers.Returns, _name='returns')
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='trades')
    
    # Ejecutar backtest
    results = cerebro.run()
    strat = results[0]
    
    # Imprimir resultados
    print('=' * 50)
    print('RESULTADOS DEL BACKTEST')
    print('=' * 50)
    print(f'Capital final: ${cerebro.broker.getvalue():.2f}')
    print(f'Retorno total: {(cerebro.broker.getvalue()/initial_cash - 1)*100:.2f}%')
    
    # Métricas de riesgo
    sharpe = strat.analyzers.sharpe.get_analysis()
    returns = strat.analyzers.returns.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    
    print(f'Ratio Sharpe: {sharpe.get("sharperatio", 0):.2f}')
    print(f'Drawdown máximo: {drawdown.max.drawdown:.2f}%')
    
    return strat