# simple_backtest.py
import backtrader as bt
import pandas as pd
from datetime import datetime

# Estrategia simple
class TestStrategy(bt.Strategy):
    def next(self):
        if not self.position:
            if self.data.close[0] > self.data.close[-1]:
                self.buy(size=0.1)
        else:
            if self.data.close[0] < self.data.close[-1]:
                self.sell(size=self.position.size)

# Datos de ejemplo
data = bt.feeds.PandasData(
    dataname=pd.DataFrame({
        'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 110]
    })
)

cerebro = bt.Cerebro()
cerebro.adddata(data)
cerebro.addstrategy(TestStrategy)
cerebro.broker.setcash(10000)

print('Capital inicial: %.2f' % cerebro.broker.getvalue())
results = cerebro.run()
print('Capital final: %.2f' % cerebro.broker.getvalue())
cerebro.plot()