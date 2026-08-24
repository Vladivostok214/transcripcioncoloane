"""
Servidor Local para el Experimento 08: Analizador y Transcriptor Asistido (Coloane)
===================================================================================
Puerto: 8087
Proporciona la API de inferencia, cotejo morfológico, decodificación contextual
y almacenamiento aislado de transcripciones aprobadas por el usuario.
"""

import http.server
import socketserver
import os
import json
import base64
import urllib.parse
import sys
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PORT = 8087
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXP06_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '06_web_coloane'))
EXP07_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '07_anotador_palabras_ligaduras'))
EXP02_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '02_segmentacion_lineas'))

sys.path.append(BASE_DIR)
from motor_analizador import ColoaneManuscriptAnalyzer

analyzer = ColoaneManuscriptAnalyzer()

class TranscriptorHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        clean_path = urllib.parse.unquote(parsed.path)

        if clean_path == '/' or clean_path == '/index.html':
            self.path = '/index.html'
            return super().do_GET()

        elif clean_path == '/api/sample_images':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()

            samples = []
            # Muestras de palabras del Exp 07
            words_dir = os.path.join(EXP07_DIR, 'crops_palabras')
            if os.path.exists(words_dir):
                for f in sorted(os.listdir(words_dir)):
                    if f.endswith('.png'):
                        label = f.replace('.png', '').split('_')[-1]
                        samples.append({
                            "id": f,
                            "label": f"Palabra: «{label}»",
                            "source": "exp07_palabras",
                            "url": f"/crops_palabras/{f}"
                        })

            # Muestras de líneas del Exp 02
            lines_dir = os.path.join(EXP02_DIR, 'crops')
            if os.path.exists(lines_dir):
                for f in sorted(os.listdir(lines_dir))[:8]:
                    if f.endswith('.png'):
                        samples.append({
                            "id": f,
                            "label": f"Renglón: {f}",
                            "source": "exp02_lineas",
                            "url": f"/crops_lineas/{f}"
                        })

            self.wfile.write(json.dumps({"samples": samples}, ensure_ascii=False).encode('utf-8'))
            return

        elif clean_path == '/api/approved_transcriptions':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            approved = analyzer.load_approved_transcriptions()
            self.wfile.write(json.dumps({"approved_transcriptions": approved}, ensure_ascii=False).encode('utf-8'))
            return

        elif clean_path.startswith('/crops_palabras/'):
            # Servir desde Exp 07
            file_name = clean_path.replace('/crops_palabras/', '')
            target = os.path.join(EXP07_DIR, 'crops_palabras', file_name)
            if os.path.exists(target):
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                with open(target, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        elif clean_path.startswith('/crops_lineas/'):
            # Servir desde Exp 02
            file_name = clean_path.replace('/crops_lineas/', '')
            target = os.path.join(EXP02_DIR, 'crops', file_name)
            if os.path.exists(target):
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                with open(target, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        elif clean_path.startswith('/output_analisis/') or clean_path.startswith('/uploads/'):
            return super().do_GET()

        else:
            return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        clean_path = urllib.parse.unquote(parsed.path)

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')

        if clean_path == '/api/analyze':
            try:
                data = json.loads(post_data)
                session_id = str(int(time.time() * 1000))
                image_target_path = None

                # Si es una imagen de muestra del sistema
                if data.get('source_type') == 'sample':
                    sample_url = data.get('sample_url', '')
                    if sample_url.startswith('/crops_palabras/'):
                        fname = sample_url.replace('/crops_palabras/', '')
                        image_target_path = os.path.join(EXP07_DIR, 'crops_palabras', fname)
                    elif sample_url.startswith('/crops_lineas/'):
                        fname = sample_url.replace('/crops_lineas/', '')
                        image_target_path = os.path.join(EXP02_DIR, 'crops', fname)

                # Si es una imagen subida por el usuario en Base64
                elif data.get('base64_image'):
                    b64_str = data.get('base64_image')
                    if ',' in b64_str:
                        b64_str = b64_str.split(',', 1)[1]
                    img_bytes = base64.b64decode(b64_str)
                    upload_fname = f"upload_{session_id}.png"
                    image_target_path = os.path.join(BASE_DIR, 'uploads', upload_fname)
                    with open(image_target_path, 'wb') as f:
                        f.write(img_bytes)

                if not image_target_path or not os.path.exists(image_target_path):
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "No se pudo encontrar o decodificar la imagen"}).encode('utf-8'))
                    return

                # Ejecutar análisis completo
                analysis_res = analyzer.analyze_manuscript_image(image_target_path, session_id=session_id)
                analysis_res["image_name"] = os.path.basename(image_target_path)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(analysis_res, ensure_ascii=False).encode('utf-8'))
                return

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return

        elif clean_path == '/api/save_approved':
            try:
                data = json.loads(post_data)
                img_name = data.get('image_name', 'desconocido.png')
                raw_pred = data.get('raw_prediction', '')
                approved = data.get('approved_text', '')
                notes = data.get('user_notes', '')

                record = analyzer.save_approved_transcription(img_name, raw_pred, approved, notes)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "saved", "record": record}, ensure_ascii=False).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), TranscriptorHandler) as httpd:
            print("="*65)
            print(f"  🔬 ANALIZADOR Y TRANSCRIPTOR ASISTIDO (EXP 08) INICIADO")
            print(f"  👉 Abre en tu navegador: http://localhost:{PORT}")
            print("="*65)
            httpd.serve_forever()
    except OSError:
        alt_port = PORT + 1
        with socketserver.TCPServer(("", alt_port), TranscriptorHandler) as httpd:
            print("="*65)
            print(f"  🔬 ANALIZADOR ASISTIDO (EXP 08) INICIADO (Puerto alternativo)")
            print(f"  👉 Abre en tu navegador: http://localhost:{alt_port}")
            print("="*65)
            httpd.serve_forever()

if __name__ == '__main__':
    run_server()
