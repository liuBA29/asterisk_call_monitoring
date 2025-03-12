#asterisk_connection.py
import time
import paramiko
import os
from dotenv import load_dotenv


# Загружаем переменные окружения
load_dotenv()


class AsteriskConnection:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.ssh = None

    def connect(self):
        try:
            # Создаем SSH клиент
            self.client = paramiko.SSHClient()
            # Разрешаем подключение к незарегистрированным хостам (для удобства, но это нужно делать с осторожностью)
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # Подключаемся к серверу
            self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
            print("SSH connection to Asterisk server successful!")
        except Exception as e:
            print(f"Error connecting to Asterisk: {e}")
            self.client = None

    def check_connection(self):
        """ Проверка состояния соединения с Asterisk через SSH """
        if self.client:
            try:
                # Выполняем команду на сервере для проверки соединения, например, запустим команду 'asterisk -rx "core show version"'
                stdin, stdout, stderr = self.client.exec_command('asterisk -rx "core show version"')
                output = stdout.read().decode()
                if output:
                    print(f"Asterisk version:\n{output}")
                    return True
                else:
                    print("No output received from Asterisk.")
            except Exception as e:
                print(f"Error during command execution: {e}")
        return False

    def get_active_calls(self):
        """ Проверяет количество активных звонков на Asterisk (только если подключение активно) """
        if not self.client:
            return "Connection error"

        try:
            stdin, stdout, stderr = self.client.exec_command('asterisk -rx "core show channels count"')
            output = stdout.read().decode()
            if "active call" in output:
                for line in output.split("\n"):
                    if "active call" in line:
                        return line.strip()  # Например: "1 active call"
            return "No active calls"
        except Exception as e:
            print(f"Error checking active calls: {e}")
            return "Error fetching calls"


    def close_connection(self):
        if self.client:
            self.client.close()
            print("Disconnected from Asterisk.")

# Пример использования
if __name__ == "__main__":
    # Параметры подключения (их нужно настроить согласно вашему Asterisk серверу)
    host = os.getenv('ASTERISK_HOST')  # IP-адрес сервера
    port = int(os.getenv('ASTERISK_PORT', 22))  # Преобразуем порт в число
    username = os.getenv('ASTERISK_USERNAME')  # Имя пользователя для подключения
    password = os.getenv('ASTERISK_PASSWORD')  # Пароль для подключения

    # Создаем экземпляр подключения
    asterisk_conn = AsteriskConnection(host, port, username, password)

    # Подключаемся к серверу Asterisk
    try:
        while True:
            asterisk_conn.connect()

            # Проверяем состояние соединения
            if asterisk_conn.check_connection():
                print("Asterisk is connected.")
            else:
                print("Asterisk connection failed.")

            # Закрываем соединение
            asterisk_conn.close_connection()

            time.sleep(10)
    except KeyboardInterrupt:
        print("Monitoring stoped")