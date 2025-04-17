import tkinter as tk
from tkinter import scrolledtext, messagebox
import paramiko
import time
import threading
import os
import json
from pathlib import Path

# Путь к файлу конфигурации (AppData\Roaming\MyApp\config.json)
CONFIG_FILE = Path(os.getenv("APPDATA")) / "MyApp" / "config.json"
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

class CallingNumber:
    def __init__(self, host, port, username, password, output_box, status_label):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.output_box = output_box
        self.status_label = status_label
        self.client = None

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
            self.status_label.config(text="Подключение к Asterisk: ✅", fg="green")
        except Exception as e:
            self.status_label.config(text="Подключение к Asterisk: ❌", fg="red")
            self.output_box.insert(tk.END, f"[Ошибка подключения] {str(e)}\n", "error")

    def get_active_calls(self):
        if not self.client:
            self.output_box.insert(tk.END, "[!] Нет активного подключения к серверу.\n", "warning")
            return

        try:
            stdin, stdout, stderr = self.client.exec_command("asterisk -rx 'core show channels verbose'")
            output = stdout.read().decode('utf-8')
            lines = output.splitlines()

            # self.output_box.delete(1.0, tk.END)

            if not lines or len(lines) <= 2:
                self.output_box.insert(tk.END, "Нет активных звонков.\n", "info")
                return

            self.output_box.insert(tk.END, f"Обновление: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n", "timestamp")
            active_calls = 0
            for line in lines[1:-1]:
                part = line.split()

                if len(part) > 7:
                    # Попробуем извлечь номер телефона
                    number = None
                    for word in part:
                        if word.isdigit() and len(word) >= 7:  # предполагаем, что это номер телефона
                            number = word
                            break

                    # Извлекаем статус звонка
                    status = "Unknown"  # Статус по умолчанию
                    if "Ringing" in line:
                        status = "Ringing"
                    elif "Up" in line:
                        status = "Up"
                    elif "Dialing" in line:
                        status = "Dialing"
                    elif "Setup" in line:
                        status = "Setup"

                    if number:
                        duration = part[-1]  # Продолжительность звонка (последний элемент)
                        active_calls += 1
                        self.output_box.insert(tk.END, f"📞 {active_calls} call from {number} — {duration} ({status})\n",
                                               "call")
                    else:
                        # Если номер не найден, показываем сообщение
                        active_calls += 1
                        self.output_box.insert(tk.END,
                                               f"📞 {active_calls} call from unknown number — {part[-1]} ({status})\n",
                                               "call")

                else:
                    # Если строка не содержит достаточно информации для звонка, просто игнорируем ее
                    continue

            if active_calls == 0:
                self.output_box.insert(tk.END, "Нет активных звонков.\n", "info")

            self.output_box.insert(tk.END, "\n" + "-" * 70 + "\n", "separator")

        except Exception as e:
            self.output_box.insert(tk.END, f"[Ошибка выполнения команды] {str(e)}\n", "error")


def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить настройки:\n{e}")

def start_gui():
    root = tk.Tk()
    root.title("Мониторинг звонков")
    root.geometry("750x620")
    root.configure(bg="#FAF3E0")

    # Заголовок
    title_label = tk.Label(
        root, text="Мониторинг активных звонков",
        font=("Helvetica", 18, "bold"),
        bg="#FAF3E0", fg="#8C4A27", pady=15
    )
    title_label.pack()

    # Статус подключения
    status_label = tk.Label(
        root, text="Подключение к Asterisk: ➖",
        font=("Helvetica", 12),
        bg="#FAF3E0", fg="gray"
    )
    status_label.pack()

    # Панель с дополнительными кнопками (до окна звонков)
    extra_button_frame = tk.Frame(root, bg="#FAF3E0")
    extra_button_frame.pack(pady=5)

    btn1 = tk.Button(extra_button_frame, text="Текущее состояние", width=20, font=("Helvetica", 10))
    btn1.pack(side=tk.LEFT, padx=5)

    btn2 = tk.Button(extra_button_frame, text="1 кнопка", width=20, font=("Helvetica", 10))
    btn2.pack(side=tk.LEFT, padx=5)

    btn3 = tk.Button(extra_button_frame, text="3 кнопка", width=20, font=("Helvetica", 10))
    btn3.pack(side=tk.LEFT, padx=5)

    btn4 = tk.Button(extra_button_frame, text="4 кнопка", width=20, font=("Helvetica", 10))
    btn4.pack(side=tk.LEFT, padx=5)


    # Окно вывода
    output_box = scrolledtext.ScrolledText(
        root, width=90, height=12,
        font=("Courier New", 11),
        bg="#FFF9F0", fg="#333333",
        relief="solid", bd=2
    )
    output_box.tag_config("timestamp", foreground="#8C4A27", font=("Courier New", 10, "bold"))
    output_box.tag_config("separator", foreground="#CCCCCC")
    output_box.tag_config("info", foreground="#555555", font=("Courier New", 10, "italic"))
    output_box.tag_config("error", foreground="red", font=("Courier New", 10, "bold"))
    output_box.tag_config("warning", foreground="#FF6600", font=("Courier New", 10, "bold"))
    output_box.tag_config("call", foreground="#003366")
    output_box.pack(pady=10, padx=15)

    # Загрузка данных из конфигурации
    config = load_config()
    host_value = config.get("host", "")
    username_value = config.get("username", "")
    password_value = config.get("password", "")

    # Поля ввода для данных
    # Поля ввода для данных
    host_frame = tk.Frame(root, bg="#FAF3E0")
    host_frame.pack(pady=5)

    host_label = tk.Label(host_frame, text="IP Asterisk:", width=15, anchor="e")
    host_label.pack(side=tk.LEFT)

    host_entry = tk.Entry(host_frame, font=("Helvetica", 12), width=30)
    host_entry.insert(0, host_value)
    host_entry.pack(side=tk.LEFT, padx=5)

    #================
    username_frame = tk.Frame(root, bg="#FAF3E0")
    username_frame.pack(pady=5)

    username_label = tk.Label(username_frame, text="Имя пользователя:", width=15, anchor="e")
    username_label.pack(side=tk.LEFT)

    username_entry = tk.Entry(username_frame, font=("Helvetica", 12), width=30)
    username_entry.insert(0, username_value)
    username_entry.pack(side=tk.LEFT, padx=5)

    #=====

    password_frame = tk.Frame(root, bg="#FAF3E0")
    password_frame.pack(pady=5)

    password_label = tk.Label(password_frame, text="Пароль:", width=15, anchor="e")
    password_label.pack(side=tk.LEFT)

    password_entry = tk.Entry(password_frame, font=("Helvetica", 12), show="*", width=30)
    password_entry.insert(0, password_value)
    password_entry.pack(side=tk.LEFT, padx=5)

    # Кнопки
    button_frame = tk.Frame(root, bg="#FAF3E0")
    button_frame.pack(pady=10)

    def run_connection():
        host = host_entry.get()
        username = username_entry.get()
        password = password_entry.get()

        if not all([host, username, password]):
            messagebox.showwarning("Ошибка", "Все поля должны быть заполнены.")
            return

        # Спросим, хочет ли пользователь сохранить данные
        if messagebox.askyesno("Сохранить?", "Сохранить введённые данные для следующего запуска? Пароль будет сохранен в открытом виде"):
            save_config({"host": host, "username": username, "password": password})
        else:
            save_config({"host": host, "username": username})  # пароль не сохраняем

        caller = CallingNumber(host, 22, username, password, output_box, status_label)
        caller.connect()

        if caller.client:
            connect_button.config(state=tk.DISABLED)

        def periodic_check():
            while True:
                caller.get_active_calls()
                time.sleep(3)

        threading.Thread(target=periodic_check, daemon=True).start()

    connect_button = tk.Button(
        button_frame, text="🔌 Подключиться",
        font=("Helvetica", 12, "bold"), command=run_connection,
        bg="#F5A623", fg="white", relief="raised", bd=2, width=18
    )
    connect_button.pack(side=tk.LEFT, padx=20)

    exit_button = tk.Button(
        button_frame, text="🚪 Выход",
        font=("Helvetica", 12, "bold"), command=root.quit,
        bg="#D9534F", fg="white", relief="raised", bd=2, width=10
    )
    exit_button.pack(side=tk.LEFT, padx=20)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
