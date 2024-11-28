import telebot
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
from bybit_api import BybitManager, run_scheduler
from logger import Logger

# Загрузка конфигурации
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Инициализация бота
bot = telebot.TeleBot(config['BOT_TOKEN'])
logger = Logger()

# Имитация базы данных
class Database:
    def __init__(self):
        self.users = {}
        self.bybit = BybitManager()
        self._lock = threading.Lock()
        
        # Запускаем обновление данных в отдельном потоке
        self.update_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.update_thread.start()
        
    def get_user(self, user_id):
        with self._lock:
            if user_id not in self.users:
                self.users[user_id] = {
                    'balance': 10000,  # Начальный баланс
                    'positions': {}    # Открытые позиции
                }
            return self.users[user_id]

# Обработчики команд бота
@bot.message_handler(commands=['start'])
def start(message):
    web_app_url = config['WEBAPP_URL']
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        text="Открыть биржу",
        web_app={"url": web_app_url}
    ))
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в учебную биржу! Нажмите кнопку ниже, чтобы начать торговлю:",
        reply_markup=markup
    )

class ExchangeHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        with open('index.html', 'rb') as f:
            self.wfile.write(f.read())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        response = {'status': 'error', 'message': 'Unknown action'}
        
        try:
            user_id = data.get('user_id')
            action = data.get('action')
            
            if action == 'get_balance':
                user_data = db.get_user(user_id)
                response = {
                    'status': 'success',
                    'balance': user_data['balance'],
                    'positions': user_data['positions']
                }
            elif action in ['buy', 'sell']:
                # Обработка торговых операций
                symbol = data.get('symbol')
                amount = float(data.get('amount', 0))
                
                user_data = db.get_user(user_id)
                current_price = db.bybit.get_price(symbol)
                
                if action == 'buy' and user_data['balance'] >= amount * current_price:
                    # Покупка
                    user_data['balance'] -= amount * current_price
                    user_data['positions'][symbol] = user_data['positions'].get(symbol, 0) + amount
                    response = {'status': 'success', 'message': 'Purchase successful'}
                elif action == 'sell' and user_data['positions'].get(symbol, 0) >= amount:
                    # Продажа
                    user_data['balance'] += amount * current_price
                    user_data['positions'][symbol] -= amount
                    response = {'status': 'success', 'message': 'Sale successful'}
                else:
                    response = {'status': 'error', 'message': 'Insufficient funds or position'}
                    
            logger.log_user_action(user_id, action, data)
                    
        except Exception as e:
            error_msg = str(e)
            logger.log_error(action, error_msg)
            response = {'status': 'error', 'message': error_msg}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

db = Database()

def run_server():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, ExchangeHandler)
    print('Starting server on port 8000...')
    httpd.serve_forever()

def main():
    # Запускаем веб-сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Запускаем бота
    print('Starting Telegram bot...')
    bot.polling(none_stop=True)

if __name__ == '__main__':
    main()