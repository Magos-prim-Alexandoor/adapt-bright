import tkinter as tk
from tkinter import ttk
import threading
import time
import numpy as np
import mss
import screen_brightness_control as sbc

# глобальные переменные
target_luminance = None
base_brightness = None
use_center = None
run_adjustment = False
freq = 10 # Частота опроса
T = 1/freq
def get_screen_luminance():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # первый экран
        screenshot = np.array(sct.grab(monitor))[:, :, :3]

        if use_center.get():
            h, w, _ = screenshot.shape
            h0, h1 = h // 4, 3 * h // 4
            w0, w1 = w // 4, 3 * w // 4
            screenshot = screenshot[h0:h1, w0:w1]

        gray = np.dot(screenshot[..., :3], [0.299, 0.587, 0.114])
        return np.mean(gray)


def save_target():
    global target_luminance, base_brightness
    target_luminance = get_screen_luminance()
    try:
        base_brightness = sbc.get_brightness(display=0)[0]
        status_var.set(f"Целевая яркость пикселей сохранена: {target_luminance:.2f}, текущая яркость экрана: {base_brightness}%")
    except Exception as e:
        status_var.set(f"Ошибка при чтении яркости: {e}")


def adjust_loop():
    global run_adjustment
    while run_adjustment:
        if target_luminance is None or base_brightness is None:
            time.sleep(1)
            continue

        current_luminance = get_screen_luminance()
        delta = current_luminance - target_luminance

        if abs(delta) > 5:  # фильтр мелких колебаний
            try:
                cur_brightness = sbc.get_brightness(display=0)[0]
                # коррекция относительно базовой яркости и разницы пикселей
                new_brightness = base_brightness - (delta / 255 * 100)
                new_brightness = max(0, min(100, new_brightness))
                sbc.set_brightness(new_brightness, display=0)
                status_var.set(f"Яркость пикселей: {current_luminance:.1f}, корректировка экрана: {new_brightness:.1f}%")
            except Exception as e:
                status_var.set(f"Ошибка: {e}")
        time.sleep(T)


def start_adjustment():
    global run_adjustment
    if target_luminance is None or base_brightness is None:
        status_var.set("Сначала зафиксируй целевую яркость!")
        return
    run_adjustment = True
    threading.Thread(target=adjust_loop, daemon=True).start()
    status_var.set("Коррекция запущена")


def stop_adjustment():
    global run_adjustment
    run_adjustment = False
    status_var.set("Остановлено")


# GUI
root = tk.Tk()
root.title("Адаптивная яркость")

use_center = tk.BooleanVar(value=False)

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

chk = ttk.Checkbutton(frame, text="Только центральные 50%", variable=use_center)
chk.pack(pady=5)

btn_save = ttk.Button(frame, text="Запомнить целевую яркость", command=save_target)
btn_save.pack(fill="x", pady=5)

btn_start = ttk.Button(frame, text="Старт коррекции", command=start_adjustment)
btn_start.pack(fill="x", pady=5)

btn_stop = ttk.Button(frame, text="Стоп", command=stop_adjustment)
btn_stop.pack(fill="x", pady=5)

status_var = tk.StringVar(value="Готово")
status_lbl = ttk.Label(frame, textvariable=status_var)
status_lbl.pack(pady=10)

root.mainloop()