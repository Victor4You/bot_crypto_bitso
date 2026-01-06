# test_advanced_imports.py
try:
    import ccxt
    import pandas as pd
    import numpy as np
    import talib  # o import ta
    from dotenv import load_dotenv
    import schedule
    import websocket
    from sklearn import linear_model
    
    print("✅ ¡Todas las importaciones del bot avanzado funcionan!")
    print(f"Pandas: {pd.__version__}")
    print(f"NumPy: {np.__version__}")
    print(f"CCXT: {ccxt.__version__}")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("Necesitas instalar: ", e.name)