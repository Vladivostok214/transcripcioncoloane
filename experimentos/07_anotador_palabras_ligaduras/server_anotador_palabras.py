"""
Servidor Backend Local para el Experimento 07: Anotador de Palabras Manuscritas (Coloane)
========================================================================================
Puerto por defecto: 8085
Permite catalogar y guardar directamente en disco recortes de palabras completas en RGB y RGBA.
"""

import http.server
import socketserver
import os
import json
import base64
import csv
import sys
from urllib.parse import urlparse

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PORT = 8085
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CROPS_DIR = os.path.join(BASE_DIR, 'crops_palabras')
CROPS_ISO_DIR = os.path.join(BASE_DIR, 'crops_palabras_isolated')
JSON_PATH = os.path.join(BASE_DIR, 'dataset_palabras_manuales.json')
CSV_PATH = os.path.join(BASE_DIR, 'dataset_palabras_manuales.csv')

for d in [CROPS_DIR, CROPS_ISO_DIR]:
    os.makedirs(d, exist_ok=True)

def load_db():
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"metadata": {"total_words": 0, "unique_words": 0}, "words": []}

def save_db(db):
    unique_words = len(set(w.get('word_text', '').lower() for w in db.get('words', [])))
    db['metadata'] = {
        "total_words": len(db.get('words', [])),
        "unique_words": unique_words,
        "last_updated": json.loads(json.dumps(None, default=str)) or ""
    }
    
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    # Actualizar CSV
    fieldnames = [
        "ID", "Capture_ID", "Word_Text", "Character_Count", "Category", "Notes",
        "BBox_X", "BBox_Y", "BBox_W", "BBox_H", "Polygon", "Crop_File", "Crop_Isolated_File", "Author", "Created_At"
    ]
    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for w in db.get('words', []):
            b = w.get('bbox', [0, 0, 0, 0])
            poly_str = json.dumps(w.get('polygon', [])) if w.get('polygon') else ""
            writer.writerow([
                w.get('id', ''),
                w.get('line_id', ''),
                w.get('word_text', ''),
                w.get('character_count', len(w.get('word_text', ''))),
                w.get('category', 'general'),
                w.get('notes', ''),
                b[0], b[1], b[2], b[3],
                poly_str,
                w.get('crop_file', ''),
                w.get('crop_isolated_file', ''),
                w.get('author', 'Colaborador'),
                w.get('created_at', '')
            ])

class WordAnnotatorHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/' or parsed.path == '/index.html':
            self.path = '/index.html'
            return super().do_GET()
        elif parsed.path == '/api/init_data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            db = load_db()
            self.wfile.write(json.dumps(db, ensure_ascii=False).encode('utf-8'))
            return
        elif parsed.path.startswith('/crops_palabras/'):
            return super().do_GET()
        elif parsed.path.startswith('/crops_palabras_isolated/'):
            return super().do_GET()
        else:
            return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/save_words':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                words = payload.get('words', [])
                db = load_db()
                existing_ids = set(w.get('id') for w in db.get('words', []))

                saved_count = 0
                for w in words:
                    # Guardar imagen RGB
                    if w.get('rgbDataUrl'):
                        raw = w['rgbDataUrl'].split(',')[1] if ',' in w['rgbDataUrl'] else w['rgbDataUrl']
                        img_bytes = base64.b64decode(raw)
                        with open(os.path.join(CROPS_DIR, w['crop_file']), 'wb') as f:
                            f.write(img_bytes)

                    # Guardar imagen RGBA aislada
                    if w.get('isoDataUrl'):
                        raw_iso = w['isoDataUrl'].split(',')[1] if ',' in w['isoDataUrl'] else w['isoDataUrl']
                        iso_bytes = base64.b64decode(raw_iso)
                        with open(os.path.join(CROPS_ISO_DIR, w['crop_isolated_file']), 'wb') as f:
                            f.write(iso_bytes)

                    # Registrar en base de datos
                    word_record = {
                        "id": w.get('id'),
                        "line_id": w.get('line_id', 'captura_externa'),
                        "word_text": w.get('word_text'),
                        "character_count": len(w.get('word_text', '')),
                        "category": w.get('category', 'general'),
                        "notes": w.get('notes', ''),
                        "author": w.get('author', 'Wladimir'),
                        "bbox": w.get('bbox', [0,0,0,0]),
                        "polygon": w.get('polygon', []),
                        "crop_file": w.get('crop_file'),
                        "crop_isolated_file": w.get('crop_isolated_file'),
                        "created_at": w.get('created_at', '')
                    }

                    if w.get('id') not in existing_ids:
                        db.setdefault('words', []).append(word_record)
                        existing_ids.add(w.get('id'))
                        saved_count += 1

                save_db(db)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "ok",
                    "saved_count": saved_count,
                    "total_words": len(db.get('words', []))
                }).encode('utf-8'))

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        elif parsed.path == '/api/delete_word':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                word_id = payload.get('id')
                db = load_db()

                target = None
                for w in db.get('words', []):
                    if w.get('id') == word_id:
                        target = w
                        break

                if target:
                    db['words'] = [w for w in db['words'] if w.get('id') != word_id]
                    save_db(db)

                    # Intentar borrar archivos de disco
                    try:
                        p1 = os.path.join(CROPS_DIR, target.get('crop_file', ''))
                        if os.path.exists(p1): os.remove(p1)
                        p2 = os.path.join(CROPS_ISO_DIR, target.get('crop_isolated_file', ''))
                        if os.path.exists(p2): os.remove(p2)
                    except Exception:
                        pass

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "db": db}).encode('utf-8'))

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), WordAnnotatorHandler) as httpd:
            print("="*65)
            print(f"  🖋️ SERVIDOR ANOTADOR DE PALABRAS (EXP 07) INICIADO")
            print(f"  👉 Abre en tu navegador: http://localhost:{PORT}")
            print("="*65)
            httpd.serve_forever()
    except OSError:
        alt_port = PORT + 1
        with socketserver.TCPServer(("", alt_port), WordAnnotatorHandler) as httpd:
            print("="*65)
            print(f"  🖋️ SERVIDOR ANOTADOR DE PALABRAS (EXP 07) INICIADO (Puerto alternativo)")
            print(f"  👉 Abre en tu navegador: http://localhost:{alt_port}")
            print("="*65)
            httpd.serve_forever()

if __name__ == '__main__':
    run_server()
