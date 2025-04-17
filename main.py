import paramiko
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from datetime import datetime

class CallingNumber:
    def __init__(self, host, port, username, password, gui_output, status_label):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.active_calls = {}  # {номер: (статус, время начала)}
        self.gui_output = gui_output  # вывод в GUI
        self.status_label = status_label  # метка статуса

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
            self.status_label.config(text="Подключение к Asterisk: ✅", fg="green")
        except Exception as e:
            self.status_label.config(text="Подключение к Asterisk: ➖", fg="gray")
            self.gui_output.insert(tk.END, f"Ошибка подключения к Asterisk: {e}\n")
            self.gui_output.yview(tk.END)
            self.client = None

    def get_active_calls(self):
        if not self.client:
            self.gui_output.insert(tk.END, "Ошибка подключения\n")
            self.gui_output.yview(tk.END)
            return
        try:
            stdin, stdout, stderr = self.client.exec_command('asterisk -rx "core show channels verbose"')
            call_info = stdout.read().decode()
            error_info = stderr.read().decode()

            if error_info:
                self.gui_output.insert(tk.END, f"Ошибка: {error_info}\n")
                self.gui_output.yview(tk.END)
                return

            current_calls = self.extract_calling_numbers(call_info)

            for number, (status, start_time) in current_calls.items():
                prev_status, prev_time = self.active_calls.get(number, ("Новый звонок", None))
                if prev_status != status:
                    self.gui_output.insert(tk.END, f"Изменение: {number} был {prev_status}, теперь {status} (Начало: {start_time})\n")
                else:
                    self.gui_output.insert(tk.END, f"Без изменений: {number} - {status} (Начало: {start_time})\n")

            for number in set(self.active_calls) - set(current_calls):
                prev_status, prev_time = self.active_calls[number]
                self.gui_output.insert(tk.END, f"Звонок завершён: {number} (был {prev_status}, начался {prev_time})\n")

            self.active_calls = current_calls  # Обновляем текущие звонки

            if current_calls:
                self.gui_output.insert(tk.END, f"Текущие звонки: {current_calls}\n")
            else:
                self.gui_output.insert(tk.END, "Нет активных звонков.\n")

            self.gui_output.yview(tk.END)
        except Exception as e:
            self.gui_output.insert(tk.END, f"Ошибка при получении активных звонков: {e}\n")
            self.gui_output.yview(tk.END)

    def extract_calling_numbers(self, call_info):
        calls = {}
        for line in call_info.splitlines():
            parts = line.split()
            if len(parts) >= 8:
                caller_id = parts[7]
                state = parts[4]
                if caller_id.isdigit():
                    start_time = self.extract_start_time(line)
                    calls[caller_id] = (state, start_time)
        return calls

    def extract_start_time(self, line):
        try:
            return datetime.now().strftime("%d-%m-%Y %H:%M")
        except Exception:
            return "Неизвестно"

    def close_connection(self):
        if self.client:
            self.client.close()


def start_gui():
    root = tk.Tk()
    root.title("Мониторинг звонков")

    host = simpledialog.askstring("Ввод данных", "Введите Asterisk Host:", parent=root)
    username = simpledialog.askstring("Ввод данных", "Введите Asterisk Username:", parent=root)
    password = simpledialog.askstring("Ввод данных", "Введите Asterisk Password:", parent=root, show='*')

    if not host or not username or not password:
        messagebox.showerror("Ошибка", "Все поля должны быть заполнены!")
        return

    status_label = tk.Label(root, text="Подключение к Asterisk: ➖", fg="gray", font=("Arial", 12))
    status_label.pack(pady=5)

    output = scrolledtext.ScrolledText(root, width=80, height=20)
    output.pack()

    calling_number = CallingNumber(host, 22, username, password, output, status_label)

    def update_calls():
        calling_number.connect()
        calling_number.get_active_calls()
        calling_number.close_connection()
        root.after(10000, update_calls)

    update_calls()
    root.mainloop()

if __name__ == "__main__":
    start_gui()
