# check_bot_status.py
import time
from advanced_bot import AdvancedTradingBot

print("=== VERIFICANDO ESTADO DEL BOT ===")
bot = AdvancedTradingBot('config_advanced.json')

# Verificar conexión
print("1. Probando conexión a exchange...")
try:
    ticker = bot.exchange.fetch_ticker('BTC/USDT')
    print(f"   ✅ Precio BTC: ${ticker['last']:.2f}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Verificar balance
print("\n2. Verificando balance...")
balance = bot.get_current_balance()
if 'USDT' in balance['total']:
    print(f"   ✅ USDT disponible: {balance['total']['USDT']}")
if 'BTC' in balance['total']:
    print(f"   ✅ BTC disponible: {balance['total']['BTC']}")

# Verificar estrategias
print("\n3. Probando motor de estrategias...")
try:
    df = bot.fetch_market_data(limit=100)
    if df is not None:
        signals = bot.strategy_engine.analyze(df)
        print(f"   ✅ Estrategias funcionando. Señales: {len(signals)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n=== RESUMEN ===")
print("Si ves 3 ✅, tu bot está listo para operar!")