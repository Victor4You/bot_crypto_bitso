import asyncio
import ccxt.async_support as ccxt_async

async def connect_websocket(self):
    """
    Sustituye el 'pass' en main.py. 
    Permite recibir precios en tiempo real sin bloquear el bot.
    """
    exchange = ccxt_async.binance({
        'apiKey': self.config['api_key'],
        'secret': self.config['api_secret'],
        'enableRateLimit': True,
    })
    
    while self.is_running:
        try:
            # Recibe el ticker en tiempo real
            ticker = await exchange.watch_ticker(self.symbol)
            current_price = ticker['last']
            
            # Verificación inmediata de Stop Loss/Take Profit 
            # sin esperar al ciclo de 5 minutos
            await self.check_open_positions(current_price)
            
        except Exception as e:
            self.logger.error(f"Error en WebSocket: {e}")
            await asyncio.sleep(5)