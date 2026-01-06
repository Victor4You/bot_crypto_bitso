# monitor_daily.py
import json
from datetime import datetime

def check_daily_performance():
    try:
        with open('trading_bot.log', 'r', encoding='utf-8') as f:
            logs = f.read()
        
        # Contadores
        buy_signals = logs.count('SEÑAL COMPRA') + logs.count('BUY')
        sell_signals = logs.count('SEÑAL VENTA') + logs.count('SELL')
        paper_trades = logs.count('PAPER TRADE')
        
        print(f"=== REPORTE DIARIO - {datetime.now().strftime('%Y-%m-%d')} ===")
        print(f"Señales COMPRA detectadas: {buy_signals}")
        print(f"Señales VENTA detectadas: {sell_signals}")
        print(f"Trades ejecutados (paper): {paper_trades}")
        print(f"Ciclos completados: {logs.count('CICLO #')}")
        
        # Extraer P&L si hay
        import re
        pnl_matches = re.findall(r'P&L = \$([\d\.]+)', logs)
        if pnl_matches:
            total_pnl = sum(float(x) for x in pnl_matches)
            print(f"P&L total: ${total_pnl:.2f}")
        
    except FileNotFoundError:
        print("Archivo de log no encontrado. El bot debe ejecutarse primero.")

if __name__ == "__main__":
    check_daily_performance()