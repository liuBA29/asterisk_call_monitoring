"""
Author: Liubov Kovaleva @liuBA29
Version: 1.0.0 (in development)
Date: 17.04.2025
License: MIT
Description: Program for call monitoring through Asterisk.

MIT License

Copyright (c) 2025 Liubov Kovaleva [@liuBA29]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import paramiko
import time
import threading
import os
import json
from pathlib import Path

# Path to the configuration file (AppData\Roaming\MyApp\config.json)
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
        self.all_calls = []

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
            self.status_label.config(text=f"Connection to Asterisk: ✅ at {time.strftime('%H:%M')} {time.strftime('%d.%m.%Y')}", fg="green")
        except Exception as e:
            self.status_label.config(text="Connection to Asterisk: ❌", fg="red")
            self.output_box.insert(tk.END, f"[Connection Error] {str(e)}\n", "error")




    def get_active_calls(self):
        global current_view
        if current_view != "current":
            return  #  Do not display information if the current view is not "current"

        if not self.client:
            self.output_box.insert(tk.END, "[!] No active connection to the server.\n", "warning")
            return

        try:

            stdin, stdout, stderr = self.client.exec_command("asterisk -rx 'core show channels verbose'")
            output = stdout.read().decode('utf-8')
            lines = output.splitlines()

            #
            self.output_box.delete(1.0, tk.END)

            #
            # for idx, call in enumerate(self.all_calls, start=1):
            #     number = call.get("number", "unknown")
            #     status = call.get("status", "Unknown")
            #     duration = call.get("duration", "0:00")
            #     self.output_box.insert(tk.END, f"📞 {idx} call from {number} — {duration} ({status})\n", "call")

            if not lines or len(lines) <= 2:
                self.output_box.insert(tk.END, "No active calls.\n", "info")
                return

            self.output_box.insert(tk.END, f"Update: {time.strftime('%d-%m-%Y %H:%M:%S')}\n\n", "timestamp")
            active_calls = 0
            for line in lines[1:-1]:
                part = line.split()

                if len(part) > 7:
                    # Attempt to extract the phone number
                    number = None
                    for word in part:
                        if word.isdigit() and len(word) >= 7:  # Assuming this is a phone number
                            number = word
                            break

                    # Extract the call status
                    status = "Unknown"
                    if "Ringing" in line:
                        status = "Ringing"
                    elif "Up" in line:
                        status = "Up"
                    elif "Dialing" in line:
                        status = "Dialing"
                    elif "Setup" in line:
                        status = "Setup"

                    if number:
                        duration = part[-1]  # Call duration (last element)
                        active_calls += 1
                        self.output_box.insert(tk.END, f"📞 {active_calls} call from {number} — {duration} ({status})\n",
                                               "call")
                        self.all_calls.append({"number": number, "status": status, "duration": duration})

                    else:
                        # If no number found, display message
                        active_calls += 1
                        self.output_box.insert(tk.END,
                                               f"📞 {active_calls} call from unknown number — {part[-1]} ({status})\n",
                                               "call")
                        self.all_calls.append({"number": "unknown", "status": status, "duration": part[-1]})

                else:
                    # Ignore lines that do not contain sufficient information for a call
                    continue

            if active_calls == 0:
                self.output_box.insert(tk.END, "No active calls.\n", "info")

            self.output_box.insert(tk.END, "\n" + "-" * 70 + "\n", "separator")

        except Exception as e:
            self.output_box.insert(tk.END, f"[Command Execution Error] {str(e)}\n", "error")


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
        messagebox.showerror("Error", f"Could not save settings:\n{e}")

def start_gui():
    root = tk.Tk()
    root.title("Call Monitoring")
    root.geometry("750x620")
    root.configure(bg="#FAF3E0")

    # Заголовок
    title_label = tk.Label(
        root, text="Active Call Monitoring",
        font=("Helvetica", 18, "bold"),
        bg="#FAF3E0", fg="#8C4A27", pady=15
    )
    title_label.pack()

    # Connection status
    status_label = tk.Label(
        root, text="Connection to Asterisk: ➖",
        font=("Helvetica", 12),
        bg="#FAF3E0", fg="gray"
    )
    status_label.pack()



    def get_current_status():
        global current_view
        current_view = "current"
        if caller and caller.client:

            #
            btn1.config(relief=tk.SUNKEN, bg="#d0d0d0")

            #

            btn2.config(relief=tk.RAISED, state=tk.NORMAL, bg="SystemButtonFace")
            btn3.config(relief=tk.RAISED, state=tk.NORMAL, bg="SystemButtonFace")
            btn4.config(relief=tk.RAISED, state=tk.NORMAL, bg="SystemButtonFace")

            caller.get_active_calls()

    def get_answered_calls():
        global current_view
        current_view = "answered"
        output_box.delete(1.0, tk.END)
        output_box.insert(tk.END, "📗 These will be **answered** calls\n", "info")
        output_box.insert(tk.END, "\n" + "-" * 70 + "\n", "separator")
        #
        btn3.config(relief=tk.SUNKEN, bg="#d0d0d0")

        #

        btn1.config(relief=tk.RAISED, state=tk.NORMAL, bg="SystemButtonFace")
        btn2.config(relief=tk.RAISED, state=tk.NORMAL, bg="SystemButtonFace")
        btn4.config(relief=tk.RAISED, state=tk.NORMAL, bg="SystemButtonFace")


    def get_missed__calls():
        global current_view
        current_view = "missed"
        output_box.delete(1.0, tk.END)
        output_box.insert(tk.END, "📕 These will be **missed** calls\n", "info")
        output_box.insert(tk.END, "\n" + "-" * 70 + "\n", "separator")

        #
        btn2.config(relief=tk.SUNKEN, bg="#d0d0d0")

        #

        btn1.config(relief=tk.RAISED, state=tk.NORMAL, bg="SystemButtonFace")
        btn3.config(relief=tk.RAISED, state=tk.NORMAL, bg="SystemButtonFace")
        btn4.config(relief=tk.RAISED, state=tk.NORMAL, bg="SystemButtonFace")

    #
    extra_button_frame = tk.Frame(root, bg="#FAF3E0")
    extra_button_frame.pack(pady=5)

    btn1 = tk.Button(extra_button_frame, text="Current Status", width=20, font=("Helvetica", 10), command=get_current_status)
    btn1.pack(side=tk.LEFT, padx=5)

    btn2 = tk.Button(extra_button_frame, text="Missed Calls", width=20, font=("Helvetica", 10), command=get_missed__calls)
    btn2.pack(side=tk.LEFT, padx=5)

    btn3 = tk.Button(extra_button_frame, text="Answered Calls", width=20, font=("Helvetica", 10), command=get_answered_calls)
    btn3.pack(side=tk.LEFT, padx=5)

    btn4 = tk.Button(extra_button_frame, text="Button 4", width=20, font=("Helvetica", 10))
    btn4.pack(side=tk.LEFT, padx=5)

    action_buttons = [btn1, btn2, btn3, btn4]
    for btn in action_buttons:
        btn.config(state=tk.DISABLED)


    #
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

    #
    config = load_config()
    host_value = config.get("host", "")
    username_value = config.get("username", "")
    password_value = config.get("password", "")

    #
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

    username_label = tk.Label(username_frame, text="Username:", width=15, anchor="e")
    username_label.pack(side=tk.LEFT)

    username_entry = tk.Entry(username_frame, font=("Helvetica", 12), width=30)
    username_entry.insert(0, username_value)
    username_entry.pack(side=tk.LEFT, padx=5)

    #=====

    password_frame = tk.Frame(root, bg="#FAF3E0")
    password_frame.pack(pady=5)

    password_label = tk.Label(password_frame, text="Password:", width=15, anchor="e")
    password_label.pack(side=tk.LEFT)

    password_entry = tk.Entry(password_frame, font=("Helvetica", 12), show="*", width=30)
    password_entry.insert(0, password_value)
    password_entry.pack(side=tk.LEFT, padx=5)

    # buttons
    button_frame = tk.Frame(root, bg="#FAF3E0")
    button_frame.pack(pady=10)




    def run_connection():
        host = host_entry.get()
        username = username_entry.get()
        password = password_entry.get()
        global caller
        caller = CallingNumber(host, 22, username, password, output_box, status_label)

        if not all([host, username, password]):
            messagebox.showwarning("Ошибка", "All fields must be filled in.")
            return

        # Спросим, хочет ли пользователь сохранить данные
        if messagebox.askyesno("Save?", "Would you like to save the entered data for the next session? The password will be stored in plain text."):
            save_config({"host": host, "username": username, "password": password})
        else:
            save_config({"host": host, "username": username})  # пароль не сохраняем

        caller = CallingNumber(host, 22, username, password, output_box, status_label)
        caller.connect()

        if caller.client:
            connect_button.config(state=tk.DISABLED)
            #
            for btn in action_buttons:
                btn.config(state=tk.NORMAL)

            #
            btn1.invoke()

        def periodic_check():
            while True:
                caller.get_active_calls()
                time.sleep(3)

        threading.Thread(target=periodic_check, daemon=True).start()

    connect_button = tk.Button(
        button_frame, text="🔌 Connect",
        font=("Helvetica", 12, "bold"), command=run_connection,
        bg="#F5A623", fg="white", relief="raised", bd=2, width=18
    )
    connect_button.pack(side=tk.LEFT, padx=20)

    exit_button = tk.Button(
        button_frame, text="🚪Exit",
        font=("Helvetica", 12, "bold"), command=root.quit,
        bg="#D9534F", fg="white", relief="raised", bd=2, width=10
    )
    exit_button.pack(side=tk.LEFT, padx=20)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
