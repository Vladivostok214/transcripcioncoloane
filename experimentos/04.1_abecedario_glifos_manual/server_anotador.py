import os
import sys
import traceback
import json
import csv
import base64
import io
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from PIL import Image
import cv2
import numpy as np

BASE_DIR = r"C:\Users\WLADI\Desktop\COLOANE\TRANSCRIPCIONES COLOANE"
EXP_DIR = os.path.join(BASE_DIR, "experimentos", "04.1_abecedario_glifos_manual")
CROPS_OUT_DIR = os.path.join(EXP_DIR, "crops")
CROPS_ISO_DIR = os.path.join(EXP_DIR, "crops_isolated")
JSON_DB_PATH = os.path.join(EXP_DIR, "dataset_glifos_manuales.json")
CSV_DB_PATH = os.path.join(EXP_DIR, "dataset_glifos_manuales.csv")
INDEX_HTML_PATH = os.path.join(EXP_DIR, "index.html")

os.makedirs(CROPS_OUT_DIR, exist_ok=True)
os.makedirs(CROPS_ISO_DIR, exist_ok=True)

def get_safe_char(char_str):
    safe = []
    for c in char_str:
        if 'a' <= c <= 'z' or 'A' <= c <= 'Z' or '0' <= c <= '9':
            safe.append(c)
        else:
            safe.append(f"u{ord(c):04x}")
    return "".join(safe)

def load_db():
    if os.path.exists(JSON_DB_PATH):
        try:
            with open(JSON_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"metadata": {"total_glyphs": 0, "captures_count": 0}, "glyphs": []}
    return {"metadata": {"total_glyphs": 0, "captures_count": 0}, "glyphs": []}

def save_db(data):
    lines_set = set(g.get("line_id") for g in data.get("glyphs", []))
    data["metadata"] = {
        "total_glyphs": len(data.get("glyphs", [])),
        "captures_count": len(lines_set),
        "last_updated": os.getenv("USERNAME", "user")
    }
    with open(JSON_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    with open(CSV_DB_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Capture_ID", "Page", "Character", "Category", "Notes", "BBox_X", "BBox_Y", "BBox_W", "BBox_H", "Polygon", "Crop_File", "Crop_Isolated_File"])
        for g in data.get("glyphs", []):
            b = g.get("bbox", [0, 0, 0, 0])
            poly = g.get("polygon", [])
            poly_str = json.dumps(poly) if poly else ""
            writer.writerow([
                g.get("id"),
                g.get("line_id"),
                g.get("page", "captura_externa"),
                g.get("character"),
                g.get("category"),
                g.get("notes", ""),
                b[0], b[1], b[2], b[3],
                poly_str,
                g.get("crop_file", ""),
                g.get("crop_isolated_file", "")
            ])

def isolate_ink(pil_img, mask=None):
    img_cv = cv2.cvtColor(np.array(pil_img.convert('RGB')), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Dynamically scale block_size for small glyphs down to 3x3
    block_size = max(3, min(21, (min(h, w) // 2) * 2 + 1))
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block_size, 10)
    
    # Only apply morphological opening on glyphs large enough to avoid eroding thin strokes
    if min(h, w) >= 20:
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    if mask is not None:
        binary[mask == 0] = 0
    
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, 0] = 240
    rgba[:, :, 1] = 240
    rgba[:, :, 2] = 240
    rgba[:, :, 3] = binary
    return Image.fromarray(rgba)

class AnnotationHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_bytes(self, content_bytes, content_type='application/json', status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content_bytes)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content_bytes)

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            raw_path = parsed.path
            path = unquote(raw_path)

            if path == '/' or path == '/index.html':
                if os.path.exists(INDEX_HTML_PATH):
                    with open(INDEX_HTML_PATH, 'rb') as f:
                        content_bytes = f.read()
                    self.send_bytes(content_bytes, 'text/html; charset=utf-8')
                else:
                    self.send_error(404, "index.html not found")

            elif path == '/api/init_data':
                db = load_db()
                data_bytes = json.dumps({'db': db}, ensure_ascii=False).encode('utf-8')
                self.send_bytes(data_bytes, 'application/json; charset=utf-8')

            elif path.startswith('/crops/'):
                filename = os.path.basename(path)
                file_path = os.path.join(CROPS_OUT_DIR, filename)
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        img_bytes = f.read()
                    self.send_bytes(img_bytes, 'image/png')
                else:
                    self.send_error(404, f"Crop not found: {filename}")

            elif path.startswith('/crops_isolated/'):
                filename = os.path.basename(path)
                file_path = os.path.join(CROPS_ISO_DIR, filename)
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        img_bytes = f.read()
                    self.send_bytes(img_bytes, 'image/png')
                else:
                    self.send_error(404, f"Isolated crop not found: {filename}")

            elif path == '/api/glyphs':
                db = load_db()
                data_bytes = json.dumps(db, ensure_ascii=False).encode('utf-8')
                self.send_bytes(data_bytes, 'application/json; charset=utf-8')

            else:
                self.send_error(404, "Not found")
        except Exception:
            traceback.print_exc()

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = unquote(parsed.path)

            if path == '/api/save_line':
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode('utf-8'))

                line_id = payload.get('line_id') or f"cap_{int(os.path.getmtime(JSON_DB_PATH)*1000)}"
                page = payload.get('page', 'captura_externa')
                boxes = payload.get('boxes', [])
                image_data = payload.get('image_data')

                if not image_data:
                    err_bytes = json.dumps({'status': 'error', 'message': 'No se recibió la imagen de la captura (image_data vacía)'}).encode('utf-8')
                    self.send_bytes(err_bytes, 'application/json', status=400)
                    return

                try:
                    b64_str = image_data.split(',', 1)[1] if ',' in image_data else image_data
                    img_bytes = base64.b64decode(b64_str)
                    pil_line = Image.open(io.BytesIO(img_bytes))
                except Exception as e:
                    err_bytes = json.dumps({'status': 'error', 'message': f'Error al decodificar la imagen: {e}'}).encode('utf-8')
                    self.send_bytes(err_bytes, 'application/json', status=400)
                    return

                if pil_line.mode not in ('RGB', 'L'):
                    pil_line = pil_line.convert('RGB')

                db = load_db()
                glyphs_list = db.get('glyphs', [])

                import time
                ts = int(time.time() * 1000)
                existing_ids = {g['id'] for g in glyphs_list}

                for i, b in enumerate(boxes):
                    bx, by, bw, bh = int(b['x']), int(b['y']), int(b['w']), int(b['h'])
                    char_str = b['character']
                    cat = b['category']
                    notes = b.get('notes', '')
                    poly = b.get('polygon', [])  # list of [x, y] points

                    safe_char = get_safe_char(char_str)
                    glyph_id = f"g_{line_id}_{i+1:02d}_{safe_char}"
                    if glyph_id in existing_ids:
                        glyph_id = f"g_{line_id}_{i+1:02d}_{ts}_{safe_char}"
                    
                    crop_filename = f"{glyph_id}.png"
                    crop_iso_filename = f"{glyph_id}_iso.png"

                    # Crop bounding box area
                    bw = max(1, bw)
                    bh = max(1, bh)
                    crop_box = (bx, by, bx + bw, by + bh)
                    cropped_img = pil_line.crop(crop_box)

                    poly_mask = None
                    if poly and len(poly) >= 3:
                        # Construct local polygon mask
                        rel_poly = np.array([[int(pt[0] - bx), int(pt[1] - by)] for pt in poly], dtype=np.int32)
                        poly_mask = np.zeros((bh, bw), dtype=np.uint8)
                        cv2.fillPoly(poly_mask, [rel_poly], 255)

                        # Mask the RGB crop: set background outside polygon to pure white
                        img_np = np.array(cropped_img.convert('RGB'))
                        img_np[poly_mask == 0] = [255, 255, 255]
                        cropped_img = Image.fromarray(img_np)

                    # Save RGB crop
                    cropped_img.save(os.path.join(CROPS_OUT_DIR, crop_filename))

                    # Save isolated ink RGBA
                    try:
                        iso_img = isolate_ink(cropped_img, mask=poly_mask)
                        iso_img.save(os.path.join(CROPS_ISO_DIR, crop_iso_filename))
                    except Exception as e:
                        print(f"Warning isolating ink for {glyph_id}: {e}", flush=True)

                    glyph_entry = {
                        "id": glyph_id,
                        "line_id": line_id,
                        "page": page,
                        "character": char_str,
                        "category": cat,
                        "notes": notes,
                        "bbox": [bx, by, bw, bh],
                        "crop_file": crop_filename,
                        "crop_isolated_file": crop_iso_filename
                    }
                    if poly and len(poly) >= 3:
                        glyph_entry["polygon"] = poly

                    glyphs_list.append(glyph_entry)

                db['glyphs'] = glyphs_list
                save_db(db)

                res_bytes = json.dumps({'status': 'ok', 'db': db, 'saved_count': len(boxes)}, ensure_ascii=False).encode('utf-8')
                self.send_bytes(res_bytes, 'application/json; charset=utf-8')

            elif path == '/api/delete_glyph':
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode('utf-8'))
                glyph_id = payload.get('id')

                db = load_db()
                glyphs_list = db.get('glyphs', [])
                db['glyphs'] = [g for g in glyphs_list if g.get('id') != glyph_id]
                save_db(db)

                res_bytes = json.dumps({'status': 'ok', 'db': db}, ensure_ascii=False).encode('utf-8')
                self.send_bytes(res_bytes, 'application/json; charset=utf-8')

            else:
                self.send_error(404, "Not found")
        except Exception:
            traceback.print_exc()

def run(port=8000):
    server = ThreadingHTTPServer(('127.0.0.1', port), AnnotationHandler)
    print(f"============================================================", flush=True)
    print(f"  ANOTADOR & BANCO DE GLIFOS COLOANE (Exp 04.1) ACTIVO", flush=True)
    print(f"  URL: http://127.0.0.1:{port}", flush=True)
    print(f"============================================================", flush=True)
    server.serve_forever()

if __name__ == '__main__':
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run(port)
