from flask import Flask, request, jsonify, send_from_directory
import requests
import base64
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'imagenA'
RESULT_FOLDER = 'videosB'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

with open('credentials.json') as f:
    creds = f.read()

creds = eval(creds)
API_URL = creds["api_url"]
TOKEN = creds["access_token"]

def encode_file_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

@app.route('/reconstruir', methods=['POST'])
def reconstruir_evento():
    prompt = request.form['descripcion']
    file = request.files['imagen']
    img_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(img_path)
    image_b64 = encode_file_to_base64(img_path)
    payload = {
        "prompt": prompt,
        "image": image_b64,
        "duration": 1
    }
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(API_URL, json=payload, headers=headers)
    if r.status_code == 200:
        video_b64 = r.json()["video"]
        video_path = os.path.join(RESULT_FOLDER, "video_generado.mp4")
        with open(video_path, "wb") as f:
            f.write(base64.b64decode(video_b64))
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "detail": r.text}), 500

@app.route('/resultado/<filename>')
def get_result(filename):
    return send_from_directory(RESULT_FOLDER, filename)
