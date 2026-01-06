import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

print(f"Probando con Token: {token[:10]}... e ID: {chat_id}")

url = f"https://api.telegram.org/bot{token}/sendMessage"
data = {"chat_id": chat_id, "text": "✅ ¡Hola! Si lees esto, Telegram está bien configurado."}

response = requests.post(url, json=data)
print(f"Respuesta de Telegram: {response.status_code}")
print(response.json())