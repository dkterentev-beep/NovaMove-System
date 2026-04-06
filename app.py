import subprocess
import sys
import sqlite3
import customtkinter as ctk

# --- ПОДГОТОВКА ---
def install_package(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_package("customtkinter")

def init_db():
    conn = sqlite3.connect('novamove.db')
    cursor = conn.cursor()
    # Таблица машин
    cursor.execute('''CREATE TABLE IF NOT EXISTS Vehicles 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, model TEXT, number TEXT, status TEXT)''')
    # Таблица заказов
    cursor.execute('''CREATE TABLE IF NOT EXISTS Orders 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       client_name TEXT, 
                       destination TEXT, 
                       vehicle_id INTEGER)''')
    conn.commit()
    conn.close()

# --- ИНТЕРФЕЙС ---
ctk.set_appearance_mode("dark") 
ctk.set_default_color_theme("blue")

class NovaMoveApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        init_db()

        self.title("NovaMove System v1.0")
        self.geometry("1000x600")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Боковое меню
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="NovaMove", font=("Arial", 24, "bold")).pack(pady=20)

        ctk.CTkButton(self.sidebar, text="🚗 Автопарк", command=self.show_cars).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="➕ Добавить авто", command=self.show_add_form).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="📝 Новый заказ", command=self.show_order_form).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="📋 Список заказов", command=self.show_orders_list).pack(pady=10, padx=20)

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.show_cars()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # --- ЛОГИКА АВТОПАРКА ---
    def show_cars(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="УПРАВЛЕНИЕ АВТОПАРКОМ", font=("Arial", 22, "bold")).pack(pady=15)
        
        conn = sqlite3.connect('novamove.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, model, number, status FROM Vehicles")
        rows = cursor.fetchall()
        conn.close()

        for car in rows:
            card = ctk.CTkFrame(self.main_frame, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5, padx=10)
            
            color = "green" if car[3] == "Свободен" else "orange"
            ctk.CTkLabel(card, text=f"ID: {car[0]} | {car[1]} ({car[2]})").pack(side="left", padx=20, pady=10)
            ctk.CTkLabel(card, text=car[3], text_color=color).pack(side="left", padx=10)
            
            btn_del = ctk.CTkButton(card, text="Удалить", width=80, fg_color="#922b21", 
                                    command=lambda cid=car[0]: self.delete_vehicle(cid))
            btn_del.pack(side="right", padx=10)

    def delete_vehicle(self, car_id):
        conn = sqlite3.connect('novamove.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Vehicles WHERE id = ?", (car_id,))
        cursor.execute("DELETE FROM Orders WHERE vehicle_id = ?", (car_id,))
        conn.commit()
        conn.close()
        self.show_cars()

    def show_add_form(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="ДОБАВЛЕНИЕ ТРАНСПОРТА", font=("Arial", 22, "bold")).pack(pady=20)
        self.entry_model = ctk.CTkEntry(self.main_frame, placeholder_text="Марка и модель", width=350, height=40)
        self.entry_model.pack(pady=10)
        self.entry_number = ctk.CTkEntry(self.main_frame, placeholder_text="Госномер", width=350, height=40)
        self.entry_number.pack(pady=10)
        ctk.CTkButton(self.main_frame, text="Сохранить", command=self.save_to_db).pack(pady=30)

    def save_to_db(self):
        m, n = self.entry_model.get(), self.entry_number.get()
        if m and n:
            conn = sqlite3.connect('novamove.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Vehicles (model, number, status) VALUES (?, ?, ?)", (m, n, "Свободен"))
            conn.commit()
            conn.close()
            self.show_cars()

    # --- ЛОГИКА ЗАКАЗОВ ---
    def show_order_form(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="ОФОРМЛЕНИЕ ЗАКАЗА", font=("Arial", 22, "bold")).pack(pady=20)

        self.entry_client = ctk.CTkEntry(self.main_frame, placeholder_text="Имя Клиента", width=350, height=40)
        self.entry_client.pack(pady=10)
        self.entry_dest = ctk.CTkEntry(self.main_frame, placeholder_text="Адрес назначения", width=350, height=40)
        self.entry_dest.pack(pady=10)

        conn = sqlite3.connect('novamove.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, model, number FROM Vehicles WHERE status = 'Свободен'")
        free_cars = cursor.fetchall()
        conn.close()

        if not free_cars:
            ctk.CTkLabel(self.main_frame, text="❌ В автопарке нет свободных машин!", text_color="red").pack()
        else:
            options = [f"{c[0]}: {c[1]} ({c[2]})" for c in free_cars]
            self.car_selector = ctk.CTkOptionMenu(self.main_frame, values=options, width=350, height=40)
            self.car_selector.pack(pady=10)
            ctk.CTkButton(self.main_frame, text="Забронировать", fg_color="green", command=self.save_order).pack(pady=20)

    def save_order(self):
        client, dest = self.entry_client.get(), self.entry_dest.get()
        car_id = self.car_selector.get().split(":")[0]

        if client and dest:
            conn = sqlite3.connect('novamove.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Orders (client_name, destination, vehicle_id) VALUES (?, ?, ?)", (client, dest, car_id))
            cursor.execute("UPDATE Vehicles SET status = 'В рейсе' WHERE id = ?", (car_id,))
            conn.commit()
            conn.close()
            self.show_orders_list()

    def show_orders_list(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="АКТИВНЫЕ РЕЙСЫ", font=("Arial", 22, "bold")).pack(pady=15)
        
        conn = sqlite3.connect('novamove.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT Orders.id, client_name, destination, Vehicles.model, Vehicles.id 
                          FROM Orders JOIN Vehicles ON Orders.vehicle_id = Vehicles.id''')
        rows = cursor.fetchall()
        conn.close()

        for order in rows:
            card = ctk.CTkFrame(self.main_frame, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5, padx=10)
            
            info = f"Заказ №{order[0]} | {order[1]} ➔ {order[2]} | Авто: {order[3]}"
            ctk.CTkLabel(card, text=info).pack(side="left", padx=20, pady=10)
            
            # Кнопка завершения: удаляет заказ и освобождает машину
            btn_finish = ctk.CTkButton(card, text="Завершить", width=100, fg_color="#2874a6",
                                       command=lambda oid=order[0], vid=order[4]: self.finish_order(oid, vid))
            btn_finish.pack(side="right", padx=10)

    def finish_order(self, order_id, vehicle_id):
        conn = sqlite3.connect('novamove.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Orders WHERE id = ?", (order_id,))
        cursor.execute("UPDATE Vehicles SET status = 'Свободен' WHERE id = ?", (vehicle_id,))
        conn.commit()
        conn.close()
        self.show_orders_list()

if __name__ == "__main__":
    app = NovaMoveApp()
    app.mainloop()
