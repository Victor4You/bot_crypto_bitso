# test_binance_fixed.py
import ccxt
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("🧪 Probando conexión con Binance Testnet...")

# Configurar exchange CON LA URL CORRECTA
exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_API_SECRET'),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot',
        'adjustForTimeDifference': True,
    }
})

# ⚠️ IMPORTANTE: Configurar testnet CORRECTAMENTE
exchange.set_sandbox_mode(True)  # ¡ESTA ES LA CLAVE!

try:
    # 1. Cargar mercados
    exchange.load_markets()
    print("✅ Conexión exitosa con Binance Testnet!")
    
    # 2. Verificar que estamos en testnet
    print(f"URL base: {exchange.urls['api']['public']}")
    
    # 3. Ver balance de prueba
    print("\n💰 Obteniendo balance de prueba...")
    balance = exchange.fetch_balance()
    
    print("📊 Fondos de prueba disponibles:")
    has_funds = False
    for currency, amount in balance['total'].items():
        if amount > 0:
            has_funds = True
            free = balance['free'].get(currency, 0)
            used = balance['used'].get(currency, 0)
            print(f"  {currency}:")
            print(f"    Total: {amount}")
            print(f"    Libre: {free}")
            print(f"    Usado: {used}")
    
    if not has_funds:
        print("  No se encontraron fondos de prueba")
        print("  Esto es normal - Binance Testnet debería darte fondos automáticamente")
    
    # 4. Ver precio BTC
    print("\n📈 Obteniendo precios...")
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"  BTC/USDT: ${ticker['last']:.2f}")
    print(f"  24h High: ${ticker['high']:.2f}")
    print(f"  24h Low: ${ticker['low']:.2f}")
    
    # 5. Probar una orden de prueba
    print("\n🔧 Probando creación de orden de prueba...")
    try:
        # Crear orden LIMIT que no se ejecutará (precio muy bajo)
        symbol = 'BTC/USDT'
        price = ticker['last'] * 0.5  # 50% del precio actual
        
        print(f"  Creando orden TEST buy 0.001 BTC @ ${price:.2f}")
        
        # Orden de prueba
        test_order = exchange.create_limit_buy_order(
            symbol=symbol,
            amount=0.001,
            price=price
        )
        print(f"  ✅ Orden creada: ID {test_order['id']}")
        
        # Cancelar orden
        exchange.cancel_order(test_order['id'], symbol)
        print("  ✅ Orden cancelada correctamente")
        
    except Exception as order_error:
        print(f"  ⚠️  No se pudo crear orden: {order_error}")
        print("  Esto puede ser normal si la API tiene restricciones")
    
    print("\n" + "="*50)
    print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
    print("="*50)
    
except ccxt.AuthenticationError as auth_error:
    print(f"\n❌ ERROR DE AUTENTICACIÓN: {auth_error}")
    print("\nVerifica:")
    print("1. API Key correcta en .env")
    print("2. Secret Key correcta en .env")
    print("3. Que hayas copiado TODAS las claves (64 chars aprox)")
    
except ccxt.NetworkError as net_error:
    print(f"\n❌ ERROR DE RED: {net_error}")
    print("Verifica tu conexión a internet")
    
except Exception as e:
    print(f"\n❌ ERROR INESPERADO: {e}")
    print(f"Tipo de error: {type(e).__name__}")