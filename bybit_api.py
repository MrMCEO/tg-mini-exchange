from pybit.unified_trading import HTTP
import json
import threading
import time
import schedule
from datetime import datetime

class BybitManager:
    def __init__(self):
        self.session = HTTP(
            testnet=False,
            api_key=None,
            api_secret=None
        )
        self.tokens_data = {}
        self._lock = threading.Lock()
        
    def update_tokens(self):
        """Обновляет информацию о всех доступных токенах"""
        try:
            # Получаем информацию о всех торговых парах
            symbols = self.session.get_instruments_info(
                category="spot"
            )
            
            if symbols and 'result' in symbols and 'list' in symbols['result']:
                with self._lock:
                    # Очищаем старые данные
                    self.tokens_data = {}
                    
                    # Обновляем информацию о каждом токене
                    for symbol in symbols['result']['list']:
                        if symbol['quoteCoin'] == 'USDT':  # Берем только пары с USDT
                            base_coin = symbol['baseCoin']
                            self.tokens_data[base_coin] = {
                                'symbol': symbol['symbol'],
                                'price': 0.0,  # Будет обновлено позже
                                'volume_24h': 0.0,  # Будет обновлено позже
                                'price_change_24h': 0.0,  # Будет обновлено позже
                                'last_update': datetime.now().isoformat()
                            }
                    
                    # Получаем текущие цены для всех пар
                    tickers = self.session.get_tickers(
                        category="spot"
                    )
                    
                    if tickers and 'result' in tickers and 'list' in tickers['result']:
                        for ticker in tickers['result']['list']:
                            symbol = ticker['symbol']
                            base_coin = symbol.replace('USDT', '')
                            if base_coin in self.tokens_data:
                                self.tokens_data[base_coin].update({
                                    'price': float(ticker['lastPrice']),
                                    'volume_24h': float(ticker['volume24h']),
                                    'price_change_24h': float(ticker.get('price24hPcnt', 0)) * 100
                                })
                    
                    # Сохраняем данные в файл
                    self.save_tokens_data()
                    
                    print(f"Данные успешно обновлены: {len(self.tokens_data)} токенов")
                    return True
            
        except Exception as e:
            print(f"Ошибка при обновлении данных: {str(e)}")
            return False
    
    def save_tokens_data(self):
        """Сохраняет данные о токенах в файл"""
        try:
            with open('tokens_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.tokens_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка при сохранении данных: {str(e)}")
    
    def load_tokens_data(self):
        """Загружает данные о токенах из файла"""
        try:
            with open('tokens_data.json', 'r', encoding='utf-8') as f:
                self.tokens_data = json.load(f)
        except FileNotFoundError:
            self.tokens_data = {}
        except Exception as e:
            print(f"Ошибка при загрузке данных: {str(e)}")
            self.tokens_data = {}
    
    def get_token_info(self, token):
        """Получает информацию о конкретном токене"""
        with self._lock:
            return self.tokens_data.get(token.upper())
    
    def get_all_tokens(self):
        """Возвращает список всех доступных токенов"""
        with self._lock:
            return list(self.tokens_data.keys())

def run_scheduler():
    """Запускает планировщик обновления данных"""
    bybit = BybitManager()
    
    # Загружаем существующие данные при запуске
    bybit.load_tokens_data()
    
    # Выполняем первое обновление сразу
    bybit.update_tokens()
    
    # Планируем обновление каждые 15 минут
    schedule.every(15).minutes.do(bybit.update_tokens)
    
    # Запускаем бесконечный цикл планировщика
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_scheduler()
