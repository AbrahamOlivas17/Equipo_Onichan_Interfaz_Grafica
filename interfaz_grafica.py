import tkinter as tk
from tkinter import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


FIELD_LENGTH = 3.60
FIELD_WIDTH = 2.80

TAGS = [
    (0, 0.0,   1.11,  "right"),
    (1, 1.230, 0.0,   "down"),
    (2, 0.0,   2.197, "right"),
    (3, 3.60,  1.038, "left"),
    (4, 2.634, 0.0,   "down"),
    (5, 2.51,  2.8,   "up"),
    (6, 1.35,  2.8,   "up"),
    (7, 3.60,  1.985, "left")
]

def dir_to_vector(direction):
    """Convierte texto -> vector de dirección"""
    if direction == "right": return (0.20, 0)
    if direction == "left":  return (-0.20, 0)
    if direction == "up":    return (0, 0.20)
    if direction == "down":  return (0, -0.20)
    return (0, 0)

# FUNCIÓN genérica para obtener posición cámara

def get_camera_position():
    """
    Reemplazar estaparn NetworkTables o JSON.
    """
    # EJEMPLO SIMULADO (moverse en un círculo)
    import math, time
    t = time.time()
    x = 1.8 + 0.8 * math.cos(t)
    y = 1.4 + 0.8 * math.sin(t)
    return x, y

# ACTUALIZAR EL PLOT

def update_plot():
    ax.clear()

    # Campo
    ax.set_title("Mapa del Campo con AprilTags y Cámara")
    ax.set_xlim(0, FIELD_LENGTH)
    ax.set_ylim(0, FIELD_WIDTH)
    ax.set_aspect("equal")
    ax.grid(True)

    # Dibujar bordes
    ax.plot(
        [0, FIELD_LENGTH, FIELD_LENGTH, 0, 0],
        [0, 0, FIELD_WIDTH, FIELD_WIDTH, 0],
        color="black"
    )

    # Dibujar Tags
    for tag_id, x, y, direction in TAGS:
        dx, dy = dir_to_vector(direction)

        ax.scatter(x, y, s=250, color="gold", edgecolor="black")
        ax.text(x, y + 0.12, f"Tag {tag_id}", ha="center")

        ax.arrow(
            x, y, dx, dy,
            head_width=0.12, head_length=0.12,
            fc="green", ec="green"
        )

    # Dibujar cámara
    cam_x, cam_y = get_camera_position()
    ax.scatter(cam_x, cam_y, s=300, color="lime")
    ax.text(cam_x, cam_y + 0.12, "CAM", ha="center", color="lime")

    canvas.draw()
    root.after(100, update_plot)


# GUI TKINTER

root = tk.Tk()
root.title("GUI AprilTags + Cámara")
root.geometry("700x600")

fig, ax = plt.subplots(figsize=(7, 5))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=BOTH, expand=True)

update_plot()
root.mainloop()