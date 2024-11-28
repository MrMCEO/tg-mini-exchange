import json
from datetime import datetime
import os

class Logger:
    def __init__(self, log_file="app.log"):
        self.log_file = log_file
        
    def log(self, event_type, data):
        """Логирование события с временной меткой"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": event_type,
            "data": data
        }
        
        with open(self.log_file, "a", encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
    def log_price_update(self, prices):
        """Логирование обновления цен"""
        self.log("price_update", prices)
        
    def log_trade(self, user_id, action, asset, amount, price):
        """Логирование торговой операции"""
        trade_data = {
            "user_id": user_id,
            "action": action,
            "asset": asset,
            "amount": amount,
            "price": price
        }
        self.log("trade", trade_data)
        
    def log_user_action(self, user_id, action, details=None):
        """Логирование действий пользователя"""
        action_data = {
            "user_id": user_id,
            "action": action,
            "details": details
        }
        self.log("user_action", action_data)
        
    def log_error(self, error_type, error_message, details=None):
        """Логирование ошибок"""
        error_data = {
            "error_type": error_type,
            "message": error_message,
            "details": details
        }
        self.log("error", error_data)
        
    def get_recent_logs(self, n=100):
        """Получение последних n записей лога"""
        if not os.path.exists(self.log_file):
            return []
            
        with open(self.log_file, "r", encoding='utf-8') as f:
            lines = f.readlines()
            logs = [json.loads(line) for line in lines[-n:]]
            return logs
            
    def clear_logs(self):
        """Очистка файла логов"""
        with open(self.log_file, "w", encoding='utf-8') as f:
            f.write("")
