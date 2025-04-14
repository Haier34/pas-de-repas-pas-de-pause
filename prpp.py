import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pyautogui
import requests
from io import BytesIO
from pystray import Icon, MenuItem, Menu
import shutil

# ---------- CONFIGURATION ----------
INACTIVITY_LIMIT = 300
MOVE_INTERVAL = 5
CONF_DIR = os.path.join(os.path.abspath("."), ".conf")
LOGO_FILENAME = "logo_interface.png"
LOGO_URL = "https://i.ibb.co/jZLt7kZR/Chat-GPT-Image-14-avr-2025-08-17-01.png"
ICON_PATH = "icon_systray.ico"
UPDATE_URL = "https://tonserveur.com/updates/mon_programme.exe"

last_mouse_position = None
last_active_time = time.time()
auto_move_enabled = True
auto_move_active = False

CURRENT_EXE = sys.executable

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def ensure_logo_exists():
    os.makedirs(CONF_DIR, exist_ok=True)
    logo_path = os.path.join(CONF_DIR, LOGO_FILENAME)
    if not os.path.exists(logo_path):
        try:
            response = requests.get(LOGO_URL)
            img = Image.open(BytesIO(response.content)).convert("RGBA")
            img = img.resize((300, 300), Image.LANCZOS)
            img.save(logo_path)
        except Exception as e:
            print(f"Erreur téléchargement logo : {e}")
    return logo_path

def check_and_update():
    try:
        print("Vérification de mise à jour...")
        response = requests.get(UPDATE_URL, stream=True)

        if response.status_code == 200:
            temp_exe = CURRENT_EXE + ".new"

            with open(temp_exe, 'wb') as f:
                shutil.copyfileobj(response.raw, f)

            backup_exe = CURRENT_EXE + ".old"
            os.rename(CURRENT_EXE, backup_exe)
            os.rename(temp_exe, CURRENT_EXE)

            print("✅ Mise à jour effectuée avec succès, redémarrage requis.")
            os.startfile(CURRENT_EXE)
            sys.exit(0)
        else:
            print("Aucune mise à jour disponible ou erreur de téléchargement.")

    except Exception as e:
        print(f"Erreur pendant la mise à jour : {e}")

def check_mouse_activity(update_ui_callback):
    global last_mouse_position, last_active_time, auto_move_active
    while True:
        current_position = pyautogui.position()
        if last_mouse_position != current_position:
            last_mouse_position = current_position
            last_active_time = time.time()
            auto_move_active = False
        else:
            if auto_move_enabled and (time.time() - last_active_time) > INACTIVITY_LIMIT:
                auto_move_active = True
        update_ui_callback()
        time.sleep(1)

def simulate_keyboard_activity():
    global auto_move_active
    while True:
        if auto_move_enabled and auto_move_active:
            pyautogui.press('shift')
        time.sleep(MOVE_INTERVAL)

def format_time(secs):
    mins, secs = divmod(int(secs), 60)
    return f"{mins:02d}:{secs:02d}"

# ---------- INTERFACE ----------
class MouseGuardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pas de repas, pas de pause 💀")
        self.root.configure(bg="white")
        self.root.geometry("500x500")
        self.root.resizable(False, False)

        logo_path = ensure_logo_exists()
        logo_path = resource_path(logo_path)
        if os.path.exists(logo_path):
            logo_image = Image.open(logo_path).convert("RGBA")
            self.tk_logo = ImageTk.PhotoImage(logo_image)
            logo_frame = tk.Frame(root, width=300, height=300, bg="white")
            logo_frame.pack(pady=(10, 0))
            self.logo_label = tk.Label(logo_frame, image=self.tk_logo, bg="white", width=300, height=300)
            self.logo_label.place(x=0, y=0)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", font=("Segoe UI", 11))
        self.style.configure("TLabel", font=("Segoe UI", 11))

        self.status_label = ttk.Label(root, text="Statut : ⏳ Initialisation...", foreground="blue", background="white")
        self.status_label.pack(pady=5)

        self.timer_label = ttk.Label(root, text="Inactivité : 00:00", background="white")
        self.timer_label.pack(pady=5)

        self.toggle_button = ttk.Button(root, text="Désactiver", command=self.toggle_auto_move)
        self.toggle_button.pack(pady=10)

        self.footer_label = ttk.Label(root, text="By Chab", font=("Segoe UI", 10, "italic"), foreground="gray", background="white")
        self.footer_label.pack(side="bottom", pady=10)

        threading.Thread(target=check_mouse_activity, args=(self.update_ui,), daemon=True).start()
        threading.Thread(target=simulate_keyboard_activity, daemon=True).start()
        self.update_ui()

    def update_ui(self):
        global last_active_time, auto_move_active
        elapsed = time.time() - last_active_time
        self.timer_label.config(text=f"Inactivité : {format_time(elapsed)}")

        if not auto_move_enabled:
            self.status_label.config(text="Statut : 🚩 Désactivé", foreground="red")
            self.toggle_button.config(text="Activer")
        elif auto_move_active:
            self.status_label.config(text="Statut : 💨 Auto-move actif", foreground="green")
            self.toggle_button.config(text="Désactiver")
        else:
            self.status_label.config(text="Statut : ✅ Surveillance", foreground="blue")
            self.toggle_button.config(text="Désactiver")

        self.root.after(1000, self.update_ui)

    def toggle_auto_move(self):
        global auto_move_enabled, auto_move_active
        auto_move_enabled = not auto_move_enabled
        auto_move_active = False

# ---------- SYSTRAY ----------
def quit_app(icon, item):
    icon.stop()
    root.quit()

def create_systray_icon():
    icon_path = resource_path(ICON_PATH)
    if os.path.exists(icon_path):
        img = Image.open(icon_path).resize((64, 64), Image.LANCZOS)
        icon = Icon("PasDePause", img, "Pas de repas, pas de pause 💀", menu=Menu(MenuItem('Quitter', quit_app)))
        threading.Thread(target=icon.run, daemon=True).start()

# ---------- MAIN ----------
if __name__ == "__main__":
    threading.Thread(target=check_and_update, daemon=True).start()
    root = tk.Tk()
    app = MouseGuardApp(root)
    create_systray_icon()
    root.mainloop()
