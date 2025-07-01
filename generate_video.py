# generate_video.py
import time
import os
import sys
import json
from google import genai
from google.genai import types
from google.oauth2 import service_account
from google.cloud import storage
import mimetypes

# --- CONFIGURACIÓN DE CREDENCIALES Y SERVICIOS ---
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "generacionvideo",
    "private_key_id": "9ff3fcc9621313bc60b005373511b1e1fdf07708",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCMHTGd21qojp31
2cFw39g9q5EFY5DANJI3E47Lp04ymMqKD77jAMXluG4VIYBemKdyXyDeFNt6J+Wg
FnqP4fuMowB75oAC/oSRTKescBz/LFX/LYtYpT67WOJoLv1Eg/vyAhpBI+lcYjv/
+VvdEt6MkcL2xqlF73EsF3h+dUTc8HfTmD6lZn2+3cmSjHxKPkxCYcEoZQsD/lNQ
M+Ob4vWc8sxQfnVWXySIgoxYNJvmXiMYchF/iSYtZxjMcLxFtelIAG9DV9Movyiv
qxrNW28/UCgUZFsIuWr7tNprZbQiBv58hYkpmlB4Y4p03TxlMdpcPmq3iK1W0Dst
zqSoCkfxAgMBAAECggEAASNX5lggBbyRnaeUdG/m4jl7+Wq/dzD/uRoZyE5jENS1
xvnNdxHsSZPEkczeguhSamTSLd9Xh+WxKbtvJIRGZk3I+CvdRY04lUSuLNciwBel
peeb8srLWG5iRmXtT0ZXon5FcgVwKydQYL9ePjuZYv6KkD4j0AHKqcBE/H9utqzj
IlAEvbq6rinbv2eeqyI9+EVmWx0z081AEBhbfAN+MCt7i9i0A82lMPykugxBgPNO
CC0cGdZR7USHkVOKXzteGJFrb+LVcacTZ7Hw1UkFPKwshRxfAL4exSAUrk+qyuG/
WrnwZ9Tal8zVWk/pO035fshoJ+2q+jtsS8p4xWkMzQKBgQDBuvqN8KL20wi3orW2
Qa26Jm0geyGPubvkuCDm1qfu776fco26MhEriYT5PmGG8tH8YDiYGW+2z4Sr3dSR
gcgKtWh6PDdYtW62G5Y/bzqwKqd9qSrw2e9f1v/OEry9HqzjFtCwPnqj+PGATHzP
8Xsjq1Ua7Lj9d00QLTlcZTCyfQKBgQC5JmrEdO2mkayB41GWqVSCso+toX4+6LE4
XWibwFwzUMcUXcSufZcEuRSeuBxREilnSrUtT622ANcNBLZUaPPoVYqsYfIs9xul
sJoSw8q/b82o6Ur6SGk2ff8+IARYZjODFmgJoBy4cEzIg8SqayqbTJ18CSBqAP/+
Dcy+AZRRhQKBgQCmcXCm1mIM0c8hhqe8CL2ruyvyxhdVlmu53ABYk4AApvYNo6vk
lvNthl86jL/Z43FJ9ZlqBCCY3b3Ms2/X+7rUiHtU2btreaW+zADQS04O4Pa53cfI
2lTw8JUihbKmgV5kVMvDQEq56j4CzrRFK+FyCde6pDtjeUY6acBog3/NOQKBgQCb
DGLotgq2LNPLyfNvOco90Q6lFtJEGFUgoIiTtdkAWCr/ES89+IpZOCzeZcvA0Ha/
uz5R/aG5AqcUjdeqhGGNNOV2Smel5CHQ9T1xbWkCO7x8MTHKuozxRz5SZjl9VcjZ
hBAHz399rP2ABWjSVgBOITDYyEPOwZuewyusCmKMiQKBgHr6WtpLsquT65HE6aSi
rVEkQu6hk8YvkBG//2hsRklVr/h4m0bEufvj0l0M+Xl7g56LAS8679uN7zH7YqWw
P1XmM9jxkriY+LfiKNNf2hC/WkLlfPTOhzNCaUW8iTj3Ht80RPh5YKEQSNUsKzgg
Rj6HVNogr4+tq4e4RoqS50T3
-----END PRIVATE KEY-----""",
    "client_email": "generacion-video-nuevo@generacionvideo.iam.gserviceaccount.com",
    "client_id": "115178613738123655779",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/generacion-video-nuevo%40generacionvideo.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

PROJECT_ID = "generacionvideo"
LOCATION = "us-central1"
video_model = "veo-2.0-generate-001"

GCS_INPUT_IMAGES_PREFIX = "Images/"
GCS_GENERATED_VIDEOS_PREFIX = "Videos/"
GCS_BUCKET_NAME = "valorantxd"

try:
    credentials = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
except Exception as e:
    print(json.dumps({"error": f"Error al cargar credenciales: {e}"}), file=sys.stderr)
    sys.exit(1)

# Inicializar cliente de Google Cloud Storage
storage_client = storage.Client(credentials=credentials, project=PROJECT_ID)
gcs_bucket = storage_client.bucket(GCS_BUCKET_NAME)

try:
    # Inicializar cliente de Vertex AI
    client = genai.Client(
        credentials=credentials,
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
except Exception as e:
    print(json.dumps({"error": f"Error al inicializar el cliente GenAI: {e}"}), file=sys.stderr)
    sys.exit(1)

def upload_to_gcs(local_file_path, destination_blob_name):
    """Sube un archivo a Google Cloud Storage a la ruta especificada."""
    blob = gcs_bucket.blob(destination_blob_name)
    try:
        mime_type, _ = mimetypes.guess_type(local_file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        blob.upload_from_filename(local_file_path, content_type=mime_type)
        gcs_uri = f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
        print(f"Archivo {local_file_path} subido a {gcs_uri} con tipo MIME: {mime_type}", file=sys.stderr)
        return gcs_uri, mime_type
    except Exception as e:
        print(f"Error al subir {local_file_path} a GCS: {e}", file=sys.stderr)
        if '403' in str(e):
            raise Exception("PermissionError: La cuenta de servicio no tiene permisos para subir archivos a GCS.")
        else:
            raise Exception(f"Error general al subir la imagen a GCS: {e}")

def generate_video_from_image(prompt, aspect_ratio, duration_seconds, local_image_path):
    base_image_name = os.path.basename(local_image_path)
    timestamp_str = time.strftime("%Y-%m-%d_%H-%M-%S")
    # Ruta completa de la imagen en GCS (incluyendo el prefijo de entrada)
    gcs_destination_image_path = f"{GCS_INPUT_IMAGES_PREFIX}{timestamp_str}_{base_image_name}"

    # --- CORRECCIÓN AQUÍ ---
    # La API de Vertex AI espera una URI completa para output_gcs_uri, incluyendo el bucket.
    # Concatenamos el GCS_BUCKET_NAME con el prefijo de salida.
    gcs_output_video_prefix = f"gs://{GCS_BUCKET_NAME}/{GCS_GENERATED_VIDEOS_PREFIX}{timestamp_str}/"

    try:
        # 1. Subir la imagen a GCS
        gcs_image_uri, image_mime_type = upload_to_gcs(local_image_path, gcs_destination_image_path)

        # 2. Crear el objeto types.Image usando la GCS URI
        image_input_obj = types.Image(gcs_uri=gcs_image_uri, mime_type=image_mime_type)
        print(f"INFO: Objeto image_input creado usando GCS URI: {gcs_image_uri}", file=sys.stderr)

        # Llamada a la API de generación de video
        operation = client.models.generate_videos(
            model=video_model,
            prompt=prompt,
            image=image_input_obj,
            config=types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                output_gcs_uri=gcs_output_video_prefix, # ¡Ahora es una URI GCS completa!
                duration_seconds=duration_seconds,
                person_generation="dont_allow",
                enhance_prompt=True,
            ),
        )

        # Poll until operation is complete
        timeout_seconds = 600
        elapsed_time = 0
        wait_interval = 15

        while not operation.done and elapsed_time < timeout_seconds:
            time.sleep(wait_interval)
            elapsed_time += wait_interval
            operation = client.operations.get(operation)
            # print(f"Operation status: {operation.metadata.state} (Elapsed: {elapsed_time}s)", file=sys.stderr)

        if not operation.done:
            raise Exception("La operación de generación de video excedió el tiempo límite.")

        if operation.response:
            video_uri = operation.response.generated_videos[0].video.uri
            return video_uri

        else:
            error_message = "Detalles del error no disponibles."
            if operation.error:
                if hasattr(operation.error, 'message'):
                    error_message = operation.error.message
                elif isinstance(operation.error, dict):
                    if 'message' in operation.error:
                        error_message = operation.error['message']
                    elif 'errors' in operation.error and operation.error['errors']:
                        error_message = operation.error['errors'][0].get('message', 'Mensaje de error no encontrado en la estructura del diccionario.')
                    else:
                        error_message = json.dumps(operation.error)
                else:
                    error_message = str(operation.error)
            raise Exception(f"Video generation failed. Operation error: {error_message}")

    except Exception as e:
        if isinstance(e, Exception) and "PermissionError" in str(e):
             raise Exception(f"Error de permisos GCS: {e}")
        else:
             raise Exception(f"Error durante la generación del video: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(json.dumps({"error": "Uso: python generate_video.py <prompt> <aspect_ratio> <duration_seconds> <local_image_path>"}), file=sys.stderr)
        sys.exit(1)

    prompt_arg = sys.argv[1]
    aspect_ratio_arg = sys.argv[2]
    duration_seconds_arg = int(sys.argv[3])
    local_image_path_arg = sys.argv[4]

    try:
        generated_uri = generate_video_from_image(prompt_arg, aspect_ratio_arg, duration_seconds_arg, local_image_path_arg)
        print(json.dumps({"videoUri": generated_uri}))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)