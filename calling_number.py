import paramiko
import os
import time
import pytz
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CallingNumber:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.previous_calls = set()

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
            print("Подключение к Asterisk успешно!")
        except Exception as e:
            print(f"Ошибка подключения к Asterisk: {e}")
            self.client = None

    def get_active_calls(self):
        if not self.client:
            return "Ошибка подключения"
        try:
            stdin, stdout, stderr = self.client.exec_command('asterisk -rx "core show channels verbose"')
            call_info = stdout.read().decode()
            error_info = stderr.read().decode()

            if error_info:
                print(f"Ошибка: {error_info}")
                return

            calling_numbers = self.extract_calling_numbers(call_info)

            #
            if call_info:
                print("Информация об активных звонках:")
                print(call_info)

            #

            if calling_numbers:
                self.write_calls_to_file(calling_numbers)
                not_answered_calls = []
                print("Входящие номера:")
                for number in calling_numbers:
                    moscow_tz = pytz.timezone('Europe/Moscow')
                    current_time = datetime.now(moscow_tz).strftime('%d-%m-%Y %H:%M:%S')
                    print("-", number, current_time)

            else:
                print("Нет активных звонков.")

        except Exception as e:
            print(f"Ошибка при получении активных звонков: {e}")

    def extract_calling_numbers(self, call_info):
        calling_numbers = []
        for line in call_info.splitlines():
            parts = line.split()
            if len(parts) >= 8:
                caller_id = parts[7]
                inner_caller_id = parts[8]
                if caller_id.isdigit():
                    calling_numbers.append(caller_id)
        return calling_numbers

    def write_calls_to_file(self, calling_numbers):
        # Путь к файлу для записи всех звонков
        file_path = "calling_files/active_calls.txt"

        # Если папка не существует, создаем её
        folder_path = os.path.dirname(file_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Получаем текущее время
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_time = datetime.now(moscow_tz)

        # Открываем файл в режиме добавления
        with open(file_path, 'a') as file:

            for number in calling_numbers:
                timestamp = current_time.strftime('%d-%m-%Y %H:%M:%S')
                if len(calling_numbers) == 1:  # и
                # Записываем номер звонящего и метку времени
                    file.write(f"- {number} {timestamp} \n")
                    print(f"Записан звонок: {number} в {timestamp}")


    def close_connection(self):
        if self.client:
            self.client.close()


if __name__ == "__main__":
    calling_number = CallingNumber(
        os.getenv("ASTERISK_HOST"),
        int(os.getenv("ASTERISK_PORT", 22)),
        os.getenv("ASTERISK_USERNAME"),
        os.getenv("ASTERISK_PASSWORD")
    )

    try:
        while True:
            calling_number.connect()
            calling_number.get_active_calls()
            calling_number.close_connection()
            time.sleep(10)  # Интервал проверки
            print('-----------------------------------------------------------------')
    except KeyboardInterrupt:
        print("Мониторинг остановлен.")
