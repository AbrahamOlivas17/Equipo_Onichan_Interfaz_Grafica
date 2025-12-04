import tkinter as tk
from tkinter import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
import math
import time

# --- CONFIGURACIÓN DE RED ---
SERVER_IP = "127.0.0.1"
SERVER_PORT = "5000"
BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

# Variables Globales (se sobrescribirán al cargar el mapa)
FIELD_LENGTH = 3.00
FIELD_WIDTH = 3.00
TAGS = [] # Ahora guardaremos tuplas: (id, x, y, dx, dy)

# --- MATEMÁTICAS: CUATERNIÓN A VECTOR ---
def quaternion_to_vector(q):
    """
    Convierte un cuaternión (diccionario con X,Y,Z,W) a un vector unitario (dx, dy)
    basado en la rotación en el eje Z (Yaw).
    """
    x = q.get('X', 0.0)
    y = q.get('Y', 0.0)
    z = q.get('Z', 0.0)
    w = q.get('W', 1.0)

    # Fórmula para obtener el ángulo Yaw (rotación z) desde cuaternión
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    # Convertir ángulo a vector director de longitud 0.20 (para la flecha)
    arrow_length = 0.20
    dx = arrow_length * math.cos(yaw)
    dy = arrow_length * math.sin(yaw)
    
    return dx, dy

# --- CARGAR MAPA DESDE EL SERVIDOR ---
def load_map_from_server():
    global FIELD_LENGTH, FIELD_WIDTH, TAGS
    
    url = f"{BASE_URL}/json"
    print(f"Intentando cargar mapa desde {url}...")
    
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            
            # Tu endpoint devuelve una lista, tomamos el primer documento
            if isinstance(data, list):
                if not data: return # Lista vacía
                map_data = data[0] # Asumimos que el primer doc es el mapa activo
            else:
                map_data = data

            # 1. Actualizar Dimensiones del Campo
            if "field" in map_data:
                FIELD_LENGTH = float(map_data["field"].get("length", 3.0))
                FIELD_WIDTH = float(map_data["field"].get("width", 3.0))
                print(f"Mapa cargado: {FIELD_LENGTH}x{FIELD_WIDTH}m")

            # 2. Actualizar Tags
            new_tags = []
            if "tags" in map_data:
                for tag in map_data["tags"]:
                    tid = tag["ID"]
                    # Coordenadas
                    tx = tag["pose"]["translation"]["x"]
                    ty = tag["pose"]["translation"]["y"]
                    
                    # Dirección (dx, dy) desde cuaternión
                    quat = tag["pose"]["rotation"]["quaternion"]
                    dx, dy = quaternion_to_vector(quat)
                    
                    # Guardamos (ID, X, Y, DX, DY)
                    # Nota: Ya no usamos "left/right", usamos el vector calculado
                    new_tags.append((tid, tx, ty, dx, dy))
                
                TAGS[:] = new_tags # Actualizamos la lista global
                print(f"Se cargaron {len(TAGS)} AprilTags.")
                
    except Exception as e:
        print(f"Error cargando mapa: {e}")
        print("Usando valores por defecto o mapa vacío.")

# Ajustar un tag al borde más cercano (Visualización)
def snap_to_wall(x, y):
    margin = 0.00 

    dist_left   = x
    dist_right  = FIELD_LENGTH - x
    dist_bottom = y
    dist_top    = FIELD_WIDTH - y

    min_dist = min(dist_left, dist_right, dist_bottom, dist_top)

    if min_dist == dist_left:   x = margin
    elif min_dist == dist_right: x = FIELD_LENGTH - margin
    elif min_dist == dist_bottom: y = margin
    else:                        y = FIELD_WIDTH - margin

    return x, y

def get_camera_position():
    try:
        response = requests.get(f"{BASE_URL}/posicion/actual", timeout=0.3)
        if response.status_code == 200:
            datos = response.json()
            return float(datos["x"]), float(datos["y"])
    except:
        pass
    return 1.5, 1.5 # Centro por defecto si falla

def update_plot():
    ax.clear()

    ax.set_title("Campo", pad=30)
    ax.set_xlim(0, FIELD_LENGTH)
    ax.set_ylim(0, FIELD_WIDTH)
    ax.set_aspect("equal")
    ax.grid(True)

    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    ax.spines['left'].set_visible(True)

    # Dibujar bordes del campo dinámicamente
    ax.plot([0, FIELD_LENGTH, FIELD_LENGTH, 0, 0],
            [0, 0, FIELD_WIDTH, FIELD_WIDTH, 0],
            color="black")

    cam_x, cam_y = get_camera_position()

    # Obtener rotación de la cámara
    rot = 0
    try:
        response = requests.get(f"{BASE_URL}/posicion/actual", timeout=0.3)
        if response.status_code == 200:
            rot = float(response.json().get("rotation", 0)) # Si tu JSON de posición incluye rotación
    except:
        pass

    # --- Lógica de FOV (Campo de Visión) ---
    # Delay anti-saturación visual
    # time.sleep(0.05) # Reduje el tiempo para que sea más fluido

    FOV_ANGLE = 60
    VIEW_DISTANCE = 3.0

    center_rad = math.radians(rot)
    left_rad = math.radians(rot + FOV_ANGLE/2)
    right_rad = math.radians(rot - FOV_ANGLE/2)

    p_left = (cam_x + VIEW_DISTANCE * math.cos(left_rad),
              cam_y + VIEW_DISTANCE * math.sin(left_rad))
    p_right = (cam_x + VIEW_DISTANCE * math.cos(right_rad),
               cam_y + VIEW_DISTANCE * math.sin(right_rad))

    ax.plot([cam_x, p_left[0]],  [cam_y, p_left[1]],  color="cyan", alpha=0.5)
    ax.plot([cam_x, p_right[0]], [cam_y, p_right[1]], color="cyan", alpha=0.5)
    ax.plot([p_left[0], p_right[0]], [p_left[1], p_right[1]], color="cyan", linestyle="dashed", alpha=0.3)

    def punto_en_fov(px, py):
        dx = px - cam_x
        dy = py - cam_y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > VIEW_DISTANCE: return False
        ang = math.degrees(math.atan2(dy, dx))
        diff = (ang - rot + 180) % 360 - 180
        return abs(diff) <= (FOV_ANGLE / 2)

    # --- DIBUJAR TAGS DINÁMICOS ---
    # Iteramos sobre la lista global TAGS que llenamos desde el JSON
    for tag_data in TAGS:
        # Desempaquetar tupla (ahora trae dx, dy directamente)
        tag_id, raw_x, raw_y, dx, dy = tag_data

        # Pegar tag a la pared (opcional, depende de si el JSON trae coordenadas exactas de pared)
        x_snap, y_snap = snap_to_wall(raw_x, raw_y)

        color_tag = "red" if punto_en_fov(x_snap, y_snap) else "gold"

        ax.scatter(x_snap, y_snap, s=250, color=color_tag, edgecolor="black")

        # Texto del Tag
        offset = 0.30
        text_x, text_y = x_snap, y_snap
        
        # Ajuste simple de etiqueta de texto para que no se encime
        if x_snap < 0.1: text_x -= offset
        elif x_snap > FIELD_LENGTH - 0.1: text_x += offset
        elif y_snap < 0.1: text_y -= offset
        elif y_snap > FIELD_WIDTH - 0.1: text_y += offset

        ax.text(text_x, text_y, f"Tag {tag_id}", ha="center", va="center", fontsize=9, fontweight='bold')

        # Dibujar flecha de dirección usando dx, dy calculados del cuaternión
        ax.arrow(x_snap, y_snap, dx, dy,
                 head_width=0.08, head_length=0.08,
                 fc="green", ec="green")

    # Dibujar Cámara
    ax.scatter(cam_x, cam_y, s=300, color="lime", zorder=5)

    canvas.draw()
    root.after(200, update_plot) # Actualizar cada 200ms

# --- GUI PRINCIPAL ---
root = tk.Tk()
root.geometry("900x700")

# 1. Cargar el mapa ANTES de iniciar la gráfica
load_map_from_server()

fig, ax = plt.subplots(figsize=(8, 6))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=BOTH, expand=True)

update_plot()
root.mainloop()