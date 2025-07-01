from flask import Flask, request, jsonify
import requests
import base64
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'imagenA'
RESULT_FOLDER = 'videosB'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

with open('credentials.json') as f:
    c = eval(f.read())

def to_b64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def save_b64(data, path):
    with open(path, 'wb') as f:
        f.write(base64.b64decode(data))

@app.route('/reconstruir', methods=['POST'])
def reconstruir():
    prompt = request.form['descripcion']
    f = request.files['imagen']
    name = f.filename
    img_path = os.path.join(UPLOAD_FOLDER, name)
    f.save(img_path)

    img_b64 = to_b64(img_path)
    gen_payload = {
        "prompt": prompt,
        "init_image": img_b64,
        "strength": 0.8,
        "seed": 48912
    }
    gen_headers = {
        "Authorization": f"Bearer {c['image_api_token']}",
        "Content-Type": "application/json"
    }
    gen_res = requests.post(c['image_api_url'], json=gen_payload, headers=gen_headers)
    if gen_res.status_code != 200:
        return jsonify({"estado": "error", "fase": "imagen", "detalle": gen_res.text}), 500

    gen_img_b64 = gen_res.json()['image']
    gen_img_path = os.path.join(RESULT_FOLDER, "imagen_generada.png")
    save_b64(gen_img_b64, gen_img_path)

    veo_payload = {
        "prompt": prompt,
        "image": gen_img_b64,
        "duration": 1
    }
    veo_headers = {
        "Authorization": f"Bearer {c['veo_token']}",
        "Content-Type": "application/json"
    }
    veo_res = requests.post(c['veo_api_url'], json=veo_payload, headers=veo_headers)
    if veo_res.status_code != 200:
        return jsonify({"estado": "error", "fase": "video", "detalle": veo_res.text}), 500

    video_b64 = veo_res.json()['video']
    video_path = os.path.join(RESULT_FOLDER, "video_generado.mp4")
    save_b64(video_b64, video_path)

    return jsonify({"estado": "ok"})
