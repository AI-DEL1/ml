import tkinter as tk
from tkinter import ttk, messagebox, font
import joblib
import numpy as np
import webbrowser
import random
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import os

class CyberDiabetesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("КИБЕР-ДИАГНОСТ 3000")
        self.root.geometry("900x700")
        self.root.resizable(False, False)
        
        self.init_db()
        
        try:
            self.warning_img = ImageTk.PhotoImage(Image.open("warning.png").resize((100, 100)))
            self.scan_img = ImageTk.PhotoImage(Image.open("scan.png").resize((150, 150)))
            self.history_img = ImageTk.PhotoImage(Image.open("history.png").resize((30, 30)))
        except:
            self.warning_img = None
            self.scan_img = None
            self.history_img = None

        self.root.configure(bg="#0a0a12", bd=0, highlightthickness=0)
        
        self.bg_color = "#0a0a12"
        self.card_bg = "#121220"
        self.neon_blue = "#00f0ff"
        self.neon_pink = "#ff00ff"
        self.neon_green = "#00ff9d"
        self.neon_yellow = "#ffe700"
        self.text_color = "#e0e0e0"
        self.border_color = "#303050"
        
        self.glitch_offset = 2
        self.scan_pos = 0
        self.pulse_phase = 0
        self.active_glitches = []
        
        try:
            model_path = os.path.join('мл_итог', 'diabetes_model.pkl')
            scaler_path = os.path.join('мл_итог', 'scaler.pkl')
            le_path = os.path.join('мл_итог', 'label_encoder.pkl')
            
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.le = joblib.load(le_path)
        except Exception as e:
            self.show_glitch_error(f"ОШИБКА ЗАГРУЗКИ: {str(e)}")
            return

        self.style = ttk.Style()
        self.style.theme_use('alt')
        
        try:
            self.title_font = font.Font(family="Courier New", size=24, weight="bold")
            self.subtitle_font = font.Font(family="Courier New", size=12)
            self.label_font = font.Font(family="Courier New", size=10)
            self.button_font = font.Font(family="Courier New", size=12, weight="bold")
            self.result_font = font.Font(family="Courier New", size=18, weight="bold")
            self.detail_font = font.Font(family="Courier New", size=12)
            self.link_font = font.Font(family="Courier New", size=10, underline=1)
        except:
            self.title_font = font.Font(family="Terminal", size=24, weight="bold")
            self.subtitle_font = font.Font(family="Terminal", size=12)

        self.main_frame = tk.Frame(root, bg=self.bg_color, bd=0)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.canvas = tk.Canvas(self.main_frame, bg=self.bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_color)
        
        self.create_grid_lines()
        
        self.scan_line = self.canvas.create_line(0, 0, 900, 0, fill=self.neon_blue, width=2)
        self.animate_scan_line()

        self.scrollable_frame.bind(
            "<Configure>", 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.create_header()
        self.create_input_form()
        self.create_result_section()
        self.create_footer()
        self.create_history_button()

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.animate_pulse()
        self.random_glitch()

    def create_grid_lines(self):
        """Create cyberpunk grid background"""
        for i in range(0, 900, 20):
            self.canvas.create_line(i, 0, i, 900, fill="#102030", width=1, tags="grid")
        for i in range(0, 900, 20):
            self.canvas.create_line(0, i, 900, i, fill="#102030", width=1, tags="grid")
            
        for _ in range(30):
            x = random.randint(0, 900)
            y = random.randint(0, 900)
            size = random.randint(1, 3)
            self.canvas.create_oval(x, y, x+size, y+size, fill=self.neon_blue, tags="grid")

    def init_db(self):
        """Инициализация базы данных SQLite"""
        self.conn = sqlite3.connect('diabetes_predictions.db')
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL,
            urea REAL NOT NULL,
            cr REAL NOT NULL,
            hba1c REAL NOT NULL,
            chol REAL NOT NULL,
            tg REAL NOT NULL,
            hdl REAL NOT NULL,
            ldl REAL NOT NULL,
            vldl REAL NOT NULL,
            bmi REAL NOT NULL,
            prediction TEXT NOT NULL,
            probability REAL NOT NULL
        )
        ''')
        self.conn.commit()

    def save_prediction(self, input_data, prediction, probability):
        """Сохранение прогноза в базу данных"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        gender = "МУЖСКОЙ" if input_data[0][0] == 1 else "ЖЕНСКИЙ"
        
        self.cursor.execute('''
        INSERT INTO predictions (
            timestamp, gender, age, urea, cr, hba1c, chol, tg, hdl, ldl, vldl, bmi, prediction, probability
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, gender, input_data[0][1], input_data[0][2], input_data[0][3], 
            input_data[0][4], input_data[0][5], input_data[0][6], input_data[0][7], 
            input_data[0][8], input_data[0][9], input_data[0][10], 
            prediction, probability
        ))
        self.conn.commit()

    def create_history_button(self):
        """Создание кнопки для просмотра истории"""
        self.history_btn = tk.Button(
            self.root, 
            image=self.history_img if self.history_img else None,
            text="ИСТОРИЯ" if not self.history_img else "",
            command=self.show_history,
            font=self.button_font,
            bg=self.card_bg,
            fg=self.neon_yellow,
            bd=0,
            activebackground="#202030",
            activeforeground=self.neon_pink
        )
        self.history_btn.place(x=20, y=20, width=100 if not self.history_img else 40, height=40)

    def show_history(self):
        """Отображение истории прогнозов"""
        history_window = tk.Toplevel(self.root)
        history_window.title("ИСТОРИЯ ПРОГНОЗОВ")
        history_window.geometry("1000x600")
        history_window.configure(bg=self.bg_color)
        
        style = ttk.Style(history_window)
        style.theme_use('alt')
        style.configure("Treeview", 
                       background=self.card_bg, 
                       foreground=self.text_color,
                       fieldbackground=self.card_bg,
                       borderwidth=0,
                       font=self.label_font)
        style.configure("Treeview.Heading", 
                       background=self.neon_blue, 
                       foreground=self.bg_color,
                       font=self.button_font)
        style.map('Treeview', background=[('selected', self.neon_pink)])
        
        self.cursor.execute("SELECT * FROM predictions ORDER BY timestamp DESC")
        records = self.cursor.fetchall()
        
        tree_frame = tk.Frame(history_window, bg=self.bg_color)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = [
            "id", "Дата", "Пол", "Возраст", "Мочевина", "Креатинин", 
            "HbA1c", "Холестерин", "Триглицериды", "ЛПВП", "ЛПНП", 
            "ЛПОНП", "ИМТ", "Прогноз"
        ]
        
        tree = ttk.Treeview(
            tree_frame, 
            columns=columns,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=80, anchor="center")
        
        tree.column("id", width=40)
        tree.column("Дата", width=120)
        tree.column("Пол", width=60)
        tree.column("Возраст", width=60)
        tree.column("Прогноз", width=80)
        
        for record in records:
            prediction = "Низкий" if record[13] == 'N' else "Высокий" if record[13] == 'Y' else "Умеренный"
            
            tree.insert("", "end", values=(
                record[0], record[1], record[2], record[3], record[4], 
                record[5], record[6], record[7], record[8], record[9], 
                record[10], record[11], record[12], prediction, f"{float(record[14])*100:.1f}%"
            ))
        
        scroll_y.config(command=tree.yview)
        scroll_x.config(command=tree.xview)
        
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        tree.pack(fill=tk.BOTH, expand=True)
        
        close_btn = tk.Button(
            history_window, 
            text="ЗАКРЫТЬ", 
            command=history_window.destroy,
            font=self.button_font,
            bg=self.card_bg,
            fg=self.neon_blue,
            bd=0,
            padx=20,
            pady=10,
            activebackground="#202030",
            activeforeground=self.neon_pink
        )
        close_btn.pack(pady=10)

    def animate_scan_line(self):
        self.scan_pos = (self.scan_pos + 5) % 900
        self.canvas.coords(self.scan_line, 0, self.scan_pos, 900, self.scan_pos)
        self.root.after(50, self.animate_scan_line)

    def animate_pulse(self):
        self.pulse_phase = (self.pulse_phase + 0.05) % (2 * 3.14159265)
        pulse_val = int((0.5 + 0.5 * abs(np.sin(self.pulse_phase)) * 255))
        pulse_color = f"#{pulse_val:02x}{pulse_val:02x}{pulse_val:02x}"
        
        self.canvas.itemconfig(self.scan_line, fill=pulse_color)
        self.root.after(100, self.animate_pulse)

    def random_glitch(self):
        for glitch in self.active_glitches:
            glitch.destroy()
        self.active_glitches = []
        
        if random.random() < 0.2:
            x = random.randint(50, 800)
            y = random.randint(50, 600)
            glitch_text = "".join([random.choice("01!@#$%&*") for _ in range(random.randint(5, 15))])
            glitch_label = tk.Label(self.canvas, text=glitch_text, 
                                   font=("Courier New", random.randint(8, 12)), 
                                   fg=random.choice([self.neon_blue, self.neon_pink, self.neon_green]),
                                   bg=self.bg_color)
            self.canvas.create_window(x, y, window=glitch_label)
            self.active_glitches.append(glitch_label)
            
            self.root.after(random.randint(200, 800), lambda: glitch_label.destroy())
        
        self.root.after(3000, self.random_glitch)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_header(self):
        header_frame = tk.Frame(self.scrollable_frame, bg=self.bg_color)
        header_frame.pack(pady=(0, 20), fill=tk.X)
        
        if self.scan_img:
            scan_label = tk.Label(header_frame, image=self.scan_img, bg=self.bg_color)
            scan_label.pack(side="left", padx=20)
        
        title_frame = tk.Frame(header_frame, bg=self.bg_color)
        title_frame.pack(side="left", expand=True)
        
        title_label1 = tk.Label(title_frame, text="КИБЕР-ДИАГНОСТ 3000",
                              font=self.title_font, bg=self.bg_color, fg=self.neon_blue)
        title_label1.pack(pady=(10, 0))
        
        title_label2 = tk.Label(title_frame, text="КИБЕР-ДИАГНОСТ 3000",
                              font=self.title_font, bg=self.bg_color, fg=self.neon_pink)
        title_label2.place(x=self.glitch_offset, y=10+self.glitch_offset)
        
        subtitle_label = tk.Label(title_frame,
                               text=">>> ВВЕДИТЕ БИОМЕТРИЧЕСКИЕ ДАННЫЕ ДЛЯ АНАЛИЗА <<<",
                               font=self.subtitle_font, bg=self.bg_color, fg=self.neon_green)
        subtitle_label.pack(pady=(5, 15))
        
        self.separator = tk.Frame(header_frame, height=2, bg=self.neon_blue)
        self.separator.pack(fill=tk.X, pady=5)

    def create_input_form(self):
        form_frame = tk.Frame(self.scrollable_frame, bg=self.bg_color)
        form_frame.pack(pady=10, fill=tk.X)
        
        frame_style = {
            'bg': self.card_bg,
            'bd': 1,
            'relief': tk.FLAT,
            'highlightbackground': self.neon_blue,
            'highlightthickness': 1,
            'padx': 15,
            'pady': 10
        }

        personal_frame = tk.LabelFrame(form_frame, text=" БИОМЕТРИЯ ", 
                                     font=self.label_font, fg=self.neon_blue,
                                     **frame_style)
        personal_frame.pack(pady=10, fill=tk.X)

        tk.Label(personal_frame, text="ПОЛ:", font=self.label_font, 
                bg=self.card_bg, fg=self.text_color).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.gender = ttk.Combobox(personal_frame, values=["ЖЕНСКИЙ", "МУЖСКОЙ"], 
                                 state="readonly", width=22, font=self.label_font)
        self.gender.grid(row=0, column=1, sticky="w", pady=5)
        self.gender.current(0)

        tk.Label(personal_frame, text="ВОЗРАСТ:", font=self.label_font, 
                bg=self.card_bg, fg=self.text_color).grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.age = ttk.Spinbox(personal_frame, from_=1, to=120, width=22, font=self.label_font)
        self.age.grid(row=1, column=1, sticky="w", pady=5)

        metrics_frame = tk.LabelFrame(form_frame, text=" БИОХИМИЧЕСКИЕ ПОКАЗАТЕЛИ ", 
                                    font=self.label_font, fg=self.neon_blue,
                                    **frame_style)
        metrics_frame.pack(pady=10, fill=tk.X)

        metrics = [
            ("МОЧЕВИНА (ммоль/л):", "urea"),
            ("КРЕАТИНИН (мкмоль/л):", "cr"),
            ("HbA1c (%):", "hba1c"),
            ("ХОЛЕСТЕРИН (ммоль/л):", "chol"),
            ("ТРИГЛИЦЕРИДЫ (ммоль/л):", "tg"),
            ("ЛПВП (ммоль/л):", "hdl"),
            ("ЛПНП (ммоль/л):", "ldl"),
            ("ЛПОНП (ммоль/л):", "vldl"),
            ("ИМТ:", "bmi")
        ]

        for i, (label, attr) in enumerate(metrics):
            tk.Label(metrics_frame, text=label, font=self.label_font, 
                    bg=self.card_bg, fg=self.text_color).grid(row=i, column=0, sticky="e", padx=5, pady=3)
            entry = ttk.Entry(metrics_frame, width=25, font=self.label_font)
            entry.grid(row=i, column=1, sticky="w", pady=3)
            setattr(self, attr, entry)

        self.insert_sample_data()

    def create_result_section(self):
        result_frame = tk.Frame(self.scrollable_frame, bg=self.bg_color)
        result_frame.pack(pady=20, fill=tk.X)

        self.predict_btn = tk.Button(result_frame, text="АНАЛИЗИРОВАТЬ", 
                                   font=self.button_font, bg=self.card_bg, 
                                   fg=self.neon_blue, bd=0, padx=30, pady=12,
                                   activebackground="#202030",
                                   activeforeground=self.neon_pink,
                                   command=self.predict_diabetes)
        self.predict_btn.pack(pady=20)
        
        self.predict_btn.bind("<Enter>", lambda e: self.predict_btn.config(fg=self.neon_pink))
        self.predict_btn.bind("<Leave>", lambda e: self.predict_btn.config(fg=self.neon_blue))

        self.result_card = tk.Frame(result_frame, bg=self.card_bg, bd=1, 
                                   relief=tk.FLAT, highlightbackground=self.neon_blue,
                                   highlightthickness=1)
        self.result_card.pack(pady=10, fill=tk.X, ipadx=20, ipady=20)
        
        if self.warning_img:
            self.warning_label = tk.Label(self.result_card, image=self.warning_img, bg=self.card_bg)
            self.warning_label.pack(pady=10)
        
        self.ascii_art = tk.Label(self.result_card, text="", font=("Courier New", 12), 
                                 bg=self.card_bg, fg=self.neon_green)
        self.ascii_art.pack(pady=10)

        self.result_label = tk.Label(self.result_card, text="", font=self.result_font, 
                                   bg=self.card_bg, fg=self.neon_blue)
        self.result_label.pack(pady=5)

        self.detail_label = tk.Label(self.result_card, text="", wraplength=400, 
                                    justify=tk.CENTER, font=self.detail_font, 
                                    bg=self.card_bg, fg=self.text_color)
        self.detail_label.pack(pady=10)

        self.links_frame = tk.Frame(result_frame, bg=self.bg_color)
        self.links_frame.pack(pady=15)
        
        self.info_link = tk.Label(self.links_frame, text=">>> ДОП. ИНФОРМАЦИЯ <<<", 
                                fg=self.neon_green, font=self.link_font, cursor="hand2", 
                                bg=self.bg_color)
        self.info_link.pack(pady=5)
        self.info_link.bind("<Button-1>", lambda e: webbrowser.open(
            "https://www.who.int/ru/news-room/fact-sheets/detail/diabetes"))
        
        self.doctor_link = tk.Label(self.links_frame, text=">>> ЗАПИСЬ К КИБЕР-ВРАЧУ <<<", 
                                  fg=self.neon_pink, font=self.link_font, cursor="hand2", 
                                  bg=self.bg_color)
        self.doctor_link.pack(pady=5)
        self.doctor_link.bind("<Button-1>", lambda e: webbrowser.open(
            "https://www.mos.ru/pgu/ru/md/"))
            
        self.result_card.pack_forget()
        self.info_link.pack_forget()
        self.doctor_link.pack_forget()

    def create_footer(self):
        footer_frame = tk.Frame(self.scrollable_frame, bg=self.bg_color)
        footer_frame.pack(pady=20, fill=tk.X)

        tk.Label(footer_frame,
               text="ВНИМАНИЕ: ЭТА СИСТЕМА НЕ ЗАМЕНЯЕТ КИБЕР-ВРАЧА. ДЛЯ ТОЧНОЙ ДИАГНОСТИКИ ОБРАТИТЕСЬ В МЕД-ЦЕНТР.",
               font=('Courier New', 8), fg=self.neon_yellow, bg=self.bg_color).pack()

        self.connection_status = tk.Label(footer_frame, text=">>> СИСТЕМА ГОТОВА К АНАЛИЗУ <<<",
                                        font=('Courier New', 9), fg=self.neon_green, bg=self.bg_color)
        self.connection_status.pack(pady=10)

    def insert_sample_data(self):
        self.age.delete(0, tk.END)
        self.age.insert(0, "35")

        sample_data = {
            "urea": "4.5",
            "cr": "60",
            "hba1c": "5.5",
            "chol": "4.8",
            "tg": "1.2",
            "hdl": "1.3",
            "ldl": "2.8",
            "vldl": "0.6",
            "bmi": "25"
        }

        for attr, value in sample_data.items():
            getattr(self, attr).delete(0, tk.END)
            getattr(self, attr).insert(0, value)

    def show_glitch_error(self, message):
        for _ in range(3):
            error_window = tk.Toplevel(self.root)
            error_window.title("СИСТЕМНАЯ ОШИБКА")
            error_window.geometry("500x200")
            error_window.configure(bg="#ff0066")
            
            label = tk.Label(error_window, text=message, 
                           font=("Courier New", 12, "bold"), 
                           bg="#ff0066", fg="#00ffcc")
            label.pack(expand=True)
            
            self.root.after(100, error_window.destroy)
            self.root.update()
        
        error_window = tk.Toplevel(self.root)
        error_window.title("СИСТЕМНАЯ ОШИБКА")
        error_window.geometry("500x200")
        error_window.configure(bg="#0a0a12")
        
        label = tk.Label(error_window, text=message, 
                       font=("Courier New", 12, "bold"), 
                       bg="#0a0a12", fg="#ff0066")
        label.pack(expand=True)
        
        btn = tk.Button(error_window, text="ПОНЯТНО", 
                      command=error_window.destroy,
                      font=("Courier New", 10),
                      bg="#121220", fg="#00f0ff",
                      activebackground="#ff00ff",
                      bd=0)
        btn.pack(pady=10)

    def predict_diabetes(self):
        try:
            self.connection_status.config(text=">>> АНАЛИЗ ДАННЫХ... <<<", fg=self.neon_yellow)
            self.root.update()
            
            self.result_card.pack_forget()
            self.info_link.pack_forget()
            self.doctor_link.pack_forget()

            input_data = np.array([
                [1 if self.gender.get() == 'МУЖСКОЙ' else 0],
                [float(self.age.get())],
                [float(self.urea.get())],
                [float(self.cr.get())],
                [float(self.hba1c.get())],
                [float(self.chol.get())],
                [float(self.tg.get())],
                [float(self.hdl.get())],
                [float(self.ldl.get())],
                [float(self.vldl.get())],
                [float(self.bmi.get())]
            ]).reshape(1, -1)

            input_scaled = self.scaler.transform(input_data)

            prediction = self.model.predict(input_scaled)
            prediction_proba = self.model.predict_proba(input_scaled)

            result = self.le.inverse_transform(prediction)[0]
            probability = prediction_proba[0][prediction[0]]
            
            self.save_prediction(input_data, result, probability)

            self.result_card.pack(pady=10, fill=tk.X, ipadx=20, ipady=20)
            
            if result == 'N':
                if hasattr(self, 'warning_label'):
                    self.warning_label.pack_forget()
                self.ascii_art.config(text=r"""
  ╭──────────────╮
  │   НОРМА      │
  │Все системы в │
  │  порядке     │
  ╰──────────────╯
                """, fg=self.neon_green)
                self.result_label.config(text="РИСК НИЗКИЙ", fg=self.neon_green)
                self.detail_label.config(
                    text=f"БИОМЕТРИЯ В НОРМЕ. КИБЕР-ИММУНИТЕТ УСТОЙЧИВ.\nРЕКОМЕНДУЕТСЯ СТАНДАРТНЫЙ МОНИТОРИНГ.")
                self.info_link.pack(pady=5)
            elif result == 'Y':
                if hasattr(self, 'warning_label'):
                    self.warning_label.pack(pady=10)
                self.ascii_art.config(text=r"""
  ╭──────────────╮
  │   ⚠ ОПАСНО  │
  │ требуются    │
  │Немедленные меры│
  ╰──────────────╯
                """, fg="#ff0000")
                self.result_label.config(text="ВЫСОКИЙ РИСК", fg=self.neon_pink)
                self.detail_label.config(
                    text=f"ОБНАРУЖЕНА АНОМАЛИЯ! \nНЕОБХОДИМА НЕМЕДЛЕННАЯ КОНСУЛЬТАЦИЯ КИБЕР-ВРАЧА.")
                self.doctor_link.pack(pady=5)
            else:
                if hasattr(self, 'warning_label'):
                    self.warning_label.pack(pady=10)
                self.ascii_art.config(text=r"""
  ╭──────────────╮
  │  ◑ ВНИМАНИЕ │
  │ Требуется    │
  │ проверка     │
  ╰──────────────╯
                """, fg=self.neon_yellow)
                self.result_label.config(text="УМЕРЕННЫЙ РИСК", fg=self.neon_yellow)
                self.detail_label.config(
                    text=f"ОБНАРУЖЕНЫ ОТКЛОНЕНИЯ.\nРЕКОМЕНДУЕТСЯ КОРРЕКЦИЯ И ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ.")
                self.info_link.pack(pady=5)

            self.connection_status.config(text=">>> АНАЛИЗ ЗАВЕРШЕН <<<", fg=self.neon_green)
            self.canvas.yview_moveto(1)

        except ValueError as e:
            self.show_glitch_error("ОШИБКА: НЕКОРРЕКТНЫЕ ДАННЫЕ")
            self.connection_status.config(text=">>> ОШИБКА ВВОДА <<<", fg=self.neon_pink)
        except Exception as e:
            self.show_glitch_error(f"СИСТЕМНЫЙ СБОЙ: {str(e)}")
            self.connection_status.config(text=">>> СИСТЕМНЫЙ СБОЙ <<<", fg=self.neon_pink)

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = CyberDiabetesApp(root)
    root.mainloop()