// server.js
const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const multer = require('multer');
const fs = require('fs');

const app = express();
const port = 3000;

// Configuración de Multer
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)){
    fs.mkdirSync(uploadDir);
    console.log(`[Server] Directorio 'uploads' creado en: ${uploadDir}`);
}

const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const imageFilter = function(req, file, cb) {
    if (!file.originalname.match(/\.(jpg|jpeg|png|gif|bmp)$/i)) {
        return cb(new Error('Solo se permiten archivos de imagen'), false);
    }
    cb(null, true);
};

const upload = multer({ storage: storage, fileFilter: imageFilter });

app.use(express.static(__dirname));

app.post('/generate-video', upload.single('imageFile'), (req, res) => {
    const prompt = req.body.prompt;
    const aspectRatio = req.body.aspectRatio;
    const duration = parseInt(req.body.duration);
    const uploadedImageFile = req.file;

    if (!uploadedImageFile) {
        return res.status(400).json({ error: 'Error al subir la imagen o no se seleccionó ninguna imagen válida.' });
    }
    if (!aspectRatio || !duration) {
        return res.status(400).json({ error: 'Faltan parámetros: aspectRatio y duration son requeridos.' });
    }

    console.log(`[Server] Solicitud recibida: Prompt="${prompt}", Ratio="${aspectRatio}", Duración="${duration}"`);
    
    const imagePathForPython = uploadedImageFile.path;
    console.log(`[Server] Archivo de imagen recibido: ${uploadedImageFile.filename} en ${imagePathForPython}`);

    const pythonArgs = [
        'generate_video.py',
        prompt,
        aspectRatio,
        String(duration),
        imagePathForPython // Pasar la ruta de la imagen local al script de Python
    ];

    console.log(`[Server] Ejecutando script Python con argumentos: ${pythonArgs.join(' ')}`);

    const pythonProcess = spawn('python', pythonArgs);

    let pythonOutput = '';
    let pythonError = '';

    pythonProcess.stdout.on('data', (data) => {
        pythonOutput += data.toString();
        console.log(`[Python stdout] ${data.toString().trim()}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        pythonError += data.toString();
        console.error(`[Python stderr] ${data.toString().trim()}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`[Server] Proceso Python finalizado con código de salida: ${code}`);

        // Limpiar el archivo de imagen subido localmente
        if (uploadedImageFile && fs.existsSync(uploadedImageFile.path)) {
            fs.unlink(uploadedImageFile.path, (err) => {
                if (err) console.error(`[Server] Error al eliminar el archivo temporal ${uploadedImageFile.path}:`, err);
                else console.log(`[Server] Archivo temporal ${uploadedImageFile.path} eliminado.`);
            });
        }

        if (code === 0) {
            try {
                const result = JSON.parse(pythonOutput);
                if (result.videoUri) {
                    let videoUriToSend = result.videoUri;
                    // Si la URI de la respuesta es una GCS URI, convertirla a URL pública HTTPS
                    if (videoUriToSend.startsWith('gs://')) {
                        // Extraer el nombre del bucket y la ruta del objeto
                        const parts = videoUriToSend.substring(5).split('/'); // Elimina 'gs://' y divide por '/'
                        const bucketName = parts[0];
                        const objectPath = parts.slice(1).join('/');
                        // Construye la URL pública de Google Cloud Storage
                        videoUriToSend = `https://storage.googleapis.com/${bucketName}/${objectPath}`;
                        console.log(`[Server] URI de GCS convertida a URL pública: ${videoUriToSend}`);
                    }
                    res.json({ videoUri: videoUriToSend });
                } else {
                    console.error('[Server] El script de Python finalizó con éxito pero no devolvió una URI de video válida.');
                    res.status(500).json({ error: 'El script de Python no devolvió una URI de video válida.', pythonOutput: result });
                }
            } catch (e) {
                console.error('[Server] Error al procesar la respuesta de Python:', e);
                res.status(500).json({ error: 'Error interno del servidor al procesar la respuesta de Python.', rawOutput: pythonOutput, parseError: e.message });
            }
        } else {
            let errorMessage = 'Error desconocido en el script de Python.';
            try {
                const errorResult = JSON.parse(pythonError);
                if (errorResult.error) {
                    errorMessage = errorResult.error;
                }
            } catch (e) {
                errorMessage = pythonError || 'El script de Python falló sin un mensaje de error específico en stderr.';
            }
            console.error(`[Server] La generación de video falló en Python: ${errorMessage}`);
            res.status(500).json({ error: `La generación de video falló: ${errorMessage}` });
        }
    });

    pythonProcess.on('error', (err) => {
        console.error('[Server] Error al intentar iniciar el proceso de Python:', err);
        if (uploadedImageFile && fs.existsSync(uploadedImageFile.path)) {
            fs.unlink(uploadedImageFile.path, (unlinkErr) => {
                if (unlinkErr) console.error(`[Server] Error al eliminar el archivo temporal ${uploadedImageFile.path} tras error de inicio de Python:`, unlinkErr);
            });
        }
        res.status(500).json({ error: `No se pudo iniciar el script de Python. Asegúrate de que Python esté instalado y en tu PATH. Error: ${err.message}` });
    });
});

app.listen(port, () => {
    console.log(`\n=================================================`);
    console.log(` Servidor Node.js escuchando en http://localhost:${port}`);
    console.log(` Abre http://localhost:${port} en tu navegador.`);
    console.log(`=================================================\n`);
});