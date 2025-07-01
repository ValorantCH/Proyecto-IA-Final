# -*- coding: utf-8 -*-
# app.py
import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory, abort

# --- CONFIGURACION INICIAL ---
app = Flask(__name__)

# Definimos las rutas de las carpetas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGENES_A_PATH = os.path.join(BASE_DIR, 'imagenesA')
IMAGENES_B_PATH = os.path.join(BASE_DIR, 'imagenesB')
VIDEOS_B_PATH = os.path.join(BASE_DIR, 'videosB')
DATOS_APP_PATH = os.path.join(BASE_DIR, 'datos_app')

# Rutas a los archivos de datos
ESTADO_FILE = os.path.join(DATOS_APP_PATH, 'estado.json')
MENSAJES_FILE = os.path.join(DATOS_APP_PATH, 'mensajes.json')

# Variable en memoria para rastrear archivos ya vistos
archivos_conocidos = {
    'imagenesA': set(),
    'imagenesB': set(),
    'videosB': set()
}

# --- FUNCIONES AUXILIARES ---

def inicializar_sistema():
    # Crea carpetas
    for path in [IMAGENES_A_PATH, IMAGENES_B_PATH, VIDEOS_B_PATH, DATOS_APP_PATH]:
        os.makedirs(path, exist_ok=True)
    
    # Crea archivos de datos si no existen
    if not os.path.exists(ESTADO_FILE):
        with open(ESTADO_FILE, 'w') as f: json.dump([], f)
    if not os.path.exists(MENSAJES_FILE):
        with open(MENSAJES_FILE, 'w') as f: json.dump([], f)

    # Llena el estado inicial de archivos conocidos
    global archivos_conocidos
    archivos_conocidos['imagenesA'] = set(os.listdir(IMAGENES_A_PATH))
    archivos_conocidos['imagenesB'] = set(os.listdir(IMAGENES_B_PATH))
    archivos_conocidos['videosB'] = set(os.listdir(VIDEOS_B_PATH))


def leer_json(ruta):
    try:
        with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return []

def escribir_json(ruta, datos):
    with open(ruta, 'w', encoding='utf-8') as f: json.dump(datos, f, indent=2)

def agregar_log(tipo, mensaje):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entrada = {'timestamp': timestamp, 'mensaje': mensaje}
    ruta_archivo = ESTADO_FILE if tipo == 'estado' else MENSAJES_FILE
    datos = leer_json(ruta_archivo)
    datos.insert(0, entrada)
    escribir_json(ruta_archivo, datos)

def revisar_nuevos_archivos():
    global archivos_conocidos
    hay_cambios = False
    
    mapeo_carpetas = {'imagenesA': IMAGENES_A_PATH, 'imagenesB': IMAGENES_B_PATH, 'videosB': VIDEOS_B_PATH}
    
    for nombre_carpeta, ruta_carpeta in mapeo_carpetas.items():
        archivos_actuales = set(os.listdir(ruta_carpeta))
        nuevos_archivos = archivos_actuales - archivos_conocidos[nombre_carpeta]
        
        for archivo in nuevos_archivos:
            mensaje = f"Nuevo archivo detectado en '{nombre_carpeta}': {archivo}"
            agregar_log('estado', mensaje)
            hay_cambios = True
        
        archivos_conocidos[nombre_carpeta] = archivos_actuales
    return hay_cambios

def obtener_ultimo_archivo(directorio):
    if not os.path.exists(directorio) or not os.listdir(directorio):
        return None
    archivos = [os.path.join(directorio, f) for f in os.listdir(directorio) if os.path.isfile(os.path.join(directorio, f))]
    if not archivos: return None
    return os.path.basename(max(archivos, key=os.path.getmtime))

# --- RUTAS DE LA API (ENDPOINTS) ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subir_imagen', methods=['POST'])
def subir_imagen():
    if 'imagen' not in request.files: return jsonify({'error': 'No se encontro el archivo'}), 400
    file = request.files['imagen']
    descripcion = request.form.get('descripcion', 'Sin descripcion')
    if file.filename == '': return jsonify({'error': 'No se selecciono ningun archivo'}), 400
    
    filename = file.filename
    file.save(os.path.join(IMAGENES_A_PATH, filename))
    agregar_log('estado', f"Nueva imagen subida a 'imagenesA': {filename}.")
    agregar_log('mensaje', f"PC A subio '{filename}' con la descripcion: '{descripcion}'")
    return jsonify({'success': f'Archivo {filename} subido correctamente'}), 200

@app.route('/enviar_mensaje', methods=['POST'])
def enviar_mensaje():
    mensaje = request.get_json().get('mensaje')
    if not mensaje: return jsonify({'error': 'El mensaje no puede estar vacio'}), 400
    agregar_log('mensaje', mensaje)
    return jsonify({'success': 'Mensaje recibido'}), 200

@app.route('/obtener_actualizaciones')
def obtener_actualizaciones():
    revisar_nuevos_archivos()
    
    # Obtenemos el ultimo archivo de videoB ANTES de leer los logs
    # Esto es clave para la logica de la animacion
    ultimo_video_b_nombre = obtener_ultimo_archivo(VIDEOS_B_PATH)
    
    estado = leer_json(ESTADO_FILE)
    mensajes = leer_json(MENSAJES_FILE)
    ultimo_imagen_b = obtener_ultimo_archivo(IMAGENES_B_PATH)

    return jsonify({
        'estado': estado,
        'mensajes': mensajes,
        'ultimo_imagenB': ultimo_imagen_b,
        'ultimo_videoB': ultimo_video_b_nombre # Usamos el que ya obtuvimos
    })

# CORRECCION: Ruta de descarga
@app.route('/descargar/<path:subcarpeta>/<path:filename>')
def descargar_archivo(subcarpeta, filename):
    # El diccionario ahora solo contiene los nombres de las carpetas relativas
    carpetas_permitidas = {
        "imagenesB": "imagenesB",
        "videosB": "videosB"
    }
    if subcarpeta not in carpetas_permitidas:
        abort(404, "Carpeta no encontrada")
    
    # Usamos BASE_DIR, que es la ruta absoluta a la carpeta del script (CarpetaR)
    # y send_from_directory se encargara de construir la ruta de forma segura.
    directory_path = os.path.join(BASE_DIR, carpetas_permitidas[subcarpeta])
    
    try:
        return send_from_directory(directory_path, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404, "Archivo no encontrado")
@app.route('/limpiar_logs', methods=['POST'])
def limpiar_logs():
    """Vacia los archivos de estado y mensajes."""
    try:
        # Sobrescribe los archivos con una lista vacia
        escribir_json(ESTADO_FILE, [])
        escribir_json(MENSAJES_FILE, [])
        
        # Agrega una entrada inicial al log de estado recien limpiado
        agregar_log('estado', 'Los logs de estado y mensajes han sido limpiados.')
        
        return jsonify({'success': 'Logs limpiados correctamente'}), 200
    except Exception as e:
        print(f"Error al limpiar logs: {e}")
        return jsonify({'error': 'No se pudieron limpiar los logs en el servidor'}), 500

# --- EJECUCION DEL SERVIDOR ---

if __name__ == '__main__':
    inicializar_sistema()
    agregar_log('estado', 'El programa del servidor se ha iniciado.')
    app.run(host='0.0.0.0', port=5000, debug=False)