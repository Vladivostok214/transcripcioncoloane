"""
Servidor Backend para el Experimento 05: Interactive Glyph Spotting & Active Learning
=====================================================================================
Puerto: 8003
"""

import os
import sys
import json
import time
import base64
import traceback
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
from PIL import Image
import cv2
import numpy as np

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PORT = 8003
BASE_DIR = r"C:\Users\WLADI\Desktop\COLOANE\TRANSCRIPCIONES COLOANE"
EXP_02_DIR = os.path.join(BASE_DIR, "experimentos", "02_segmentacion_lineas")
EXP_03_DIR = os.path.join(BASE_DIR, "experimentos", "03_dataset_ground_truth")
EXP_04_1_DIR = os.path.join(BASE_DIR, "experimentos", "04.1_abecedario_glifos_manual")
EXP_04_2_DIR = os.path.join(BASE_DIR, "experimentos", "04.2_vectorizacion_glifos")
EXP_05_DIR = os.path.join(BASE_DIR, "experimentos", "05_spotting_glifos_interactivo")

PATCHES_DIR = os.path.join(EXP_05_DIR, "patches")
MEMORIA_JSON = os.path.join(EXP_05_DIR, "templates_memoria.json")
INDEX_HTML = os.path.join(EXP_05_DIR, "index.html")

os.makedirs(PATCHES_DIR, exist_ok=True)

# ----------------- Funciones de Ayuda y Procesamiento de Imagen -----------------

def load_memoria():
    if os.path.exists(MEMORIA_JSON):
        try:
            with open(MEMORIA_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_memoria(data):
    with open(MEMORIA_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def preprocess_for_matching(img_bgr):
    """Convierte imagen a escala de grises con realce de contraste CLAHE"""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return enhanced, gray

def non_max_suppression(boxes, scores, iou_thresh=0.35):
    """Aplica Non-Maximum Suppression para eliminar cajas solapadas"""
    if len(boxes) == 0:
        return []
    
    boxes = np.array(boxes)
    scores = np.array(scores)
    
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 0] + boxes[:, 2]
    y2 = boxes[:, 1] + boxes[:, 3]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    
    order = scores.argsort()[::-1]
    keep = []
    
    while order.size > 0:
        i = order[0]
        keep.append(i)
        
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        
        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= iou_thresh)[0]
        order = order[inds + 1]
        
    return keep

# ----------------- Servidor HTTP -----------------

class SpotterHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_bytes(self, content_bytes, content_type='application/json', status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content_bytes)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(content_bytes)

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = unquote(parsed.path)

            if path in ['/', '/index.html']:
                if os.path.exists(INDEX_HTML):
                    with open(INDEX_HTML, 'rb') as f:
                        self.send_bytes(f.read(), 'text/html; charset=utf-8')
                else:
                    self.send_error(404, "index.html not found")

            elif path == '/api/init_data':
                self.handle_get_init_data()

            elif path.startswith('/lines/'):
                filename = os.path.basename(path)
                fp = os.path.join(EXP_02_DIR, "crops", filename)
                if os.path.exists(fp):
                    with open(fp, 'rb') as f:
                        self.send_bytes(f.read(), 'image/png')
                else:
                    self.send_error(404, f"Line crop not found: {filename}")

            elif path.startswith('/crops/'):
                filename = os.path.basename(path)
                fp = os.path.join(EXP_04_1_DIR, "crops", filename)
                if os.path.exists(fp):
                    with open(fp, 'rb') as f:
                        self.send_bytes(f.read(), 'image/png')
                else:
                    self.send_error(404, f"Glyph crop not found: {filename}")

            elif path.startswith('/crops_isolated/'):
                filename = os.path.basename(path)
                fp = os.path.join(EXP_04_1_DIR, "crops_isolated", filename)
                if os.path.exists(fp):
                    with open(fp, 'rb') as f:
                        self.send_bytes(f.read(), 'image/png')
                else:
                    self.send_error(404, f"Isolated crop not found: {filename}")

            elif path.startswith('/patches/'):
                filename = os.path.basename(path)
                fp = os.path.join(PATCHES_DIR, filename)
                if os.path.exists(fp):
                    with open(fp, 'rb') as f:
                        self.send_bytes(f.read(), 'image/png')
                else:
                    self.send_error(404, f"Patch not found: {filename}")

            elif path.startswith('/svg/'):
                filename = os.path.basename(path)
                fp = os.path.join(EXP_04_2_DIR, "svg", filename)
                if os.path.exists(fp):
                    with open(fp, 'rb') as f:
                        self.send_bytes(f.read(), 'image/svg+xml; charset=utf-8')
                else:
                    self.send_error(404, f"SVG not found: {filename}")

            else:
                self.send_error(404, "Path not found")
        except Exception:
            traceback.print_exc()

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            if parsed.path == '/api/spot_glyph':
                self.handle_spot_glyph()
            elif parsed.path == '/api/learn_patches':
                self.handle_learn_patches()
            elif parsed.path == '/api/reset_memory':
                self.handle_reset_memory()
            else:
                self.send_error(404, "Endpoint no encontrado")
        except Exception:
            traceback.print_exc()

    def handle_get_init_data(self):
        # 1. Cargar renglones disponibles
        lines_crops_dir = os.path.join(EXP_02_DIR, "crops")
        gt_file = os.path.join(EXP_03_DIR, "dataset_muestras_p02_p03.json")
        
        gt_dict = {}
        if os.path.exists(gt_file):
            with open(gt_file, 'r', encoding='utf-8') as f:
                for row in json.load(f):
                    gt_dict[row['id']] = row

        lines_list = []
        if os.path.exists(lines_crops_dir):
            for fn in sorted(os.listdir(lines_crops_dir)):
                if fn.endswith('.png'):
                    lid = os.path.splitext(fn)[0]
                    gt = gt_dict.get(lid, {})
                    lines_list.append({
                        'id': lid,
                        'filename': fn,
                        'page': gt.get('page', 0),
                        'line_number': gt.get('line_number', 0),
                        'text': gt.get('ground_truth', gt.get('text', '')),
                        'url': f'/lines/{fn}'
                    })

        # 2. Cargar glifos del catálogo
        manual_db = os.path.join(EXP_04_1_DIR, "dataset_glifos_manuales.json")
        glyphs_list = []
        if os.path.exists(manual_db):
            with open(manual_db, 'r', encoding='utf-8') as f:
                m_data = json.load(f)
                for g in m_data.get('glyphs', []):
                    gid = g['id']
                    glyphs_list.append({
                        'id': gid,
                        'character': g.get('character', '?'),
                        'category': g.get('category', 'minuscula'),
                        'line_id': g.get('line_id', ''),
                        'bbox': g.get('bbox', [0, 0, 0, 0]),
                        'crop_url': f"/crops/{g.get('crop_file', f'{gid}.png')}",
                        'crop_isolated_url': f"/crops_isolated/{g.get('crop_isolated_file', f'{gid}_iso.png')}",
                        'svg_url': f"/svg/{gid}.svg"
                    })

        # 3. Cargar memoria de parches aprendidos
        memoria = load_memoria()

        response = {
            'lines': lines_list,
            'glyphs': glyphs_list,
            'memoria': memoria
        }
        self.send_bytes(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_spot_glyph(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        payload = json.loads(body.decode('utf-8'))

        line_id = payload.get('line_id')
        glyph_id = payload.get('glyph_id')
        char_target = payload.get('character', '')
        threshold = float(payload.get('threshold', 0.55))
        scales = payload.get('scales', [0.90, 1.0, 1.10])

        # Cargar imagen de la línea
        line_path = os.path.join(EXP_02_DIR, "crops", f"{line_id}.png")
        if not os.path.exists(line_path):
            self.send_bytes(json.dumps({'error': f'Línea {line_id} no encontrada'}).encode('utf-8'), status=404)
            return

        line_img = cv2.imread(line_path)
        lh, lw = line_img.shape[:2]
        line_dist, _ = preprocess_for_matching(line_img)

        # Cargar plantilla base del glifo
        templates = []
        
        # 1. Plantilla principal (preferir crop original RGB para correlación de escala de grises rica)
        glyph_crop_path = os.path.join(EXP_04_1_DIR, "crops", f"{glyph_id}.png")
        glyph_iso_path = os.path.join(EXP_04_1_DIR, "crops_isolated", f"{glyph_id}_iso.png")
        
        target_path = glyph_crop_path if os.path.exists(glyph_crop_path) else glyph_iso_path
        if os.path.exists(target_path):
            tmpl_bgr = cv2.imread(target_path)
            tmpl_dist, _ = preprocess_for_matching(tmpl_bgr)
            templates.append({
                'id': glyph_id,
                'type': 'base',
                'dist': tmpl_dist,
                'w': tmpl_bgr.shape[1],
                'h': tmpl_bgr.shape[0]
            })

        # 2. Plantillas adicionales aprendidas en memoria para este glifo o caracter
        memoria = load_memoria()
        learned_patches = memoria.get(glyph_id, []) + (memoria.get(char_target, []) if char_target else [])
        for p in learned_patches:
            p_file = os.path.join(PATCHES_DIR, p.get('filename', ''))
            if os.path.exists(p_file):
                p_bgr = cv2.imread(p_file)
                p_dist, _ = preprocess_for_matching(p_bgr)
                templates.append({
                    'id': p.get('id', 'learned'),
                    'type': 'learned',
                    'dist': p_dist,
                    'w': p_bgr.shape[1],
                    'h': p_bgr.shape[0]
                })

        if not templates:
            self.send_bytes(json.dumps({'error': 'No se encontraron plantillas para este glifo'}).encode('utf-8'), status=400)
            return

        all_boxes = []
        all_scores = []
        all_meta = []

        # Ejecutar Multi-Template Multi-Scale Matching
        from scipy.ndimage import maximum_filter

        for t_idx, tmpl in enumerate(templates):
            tw, th = tmpl['w'], tmpl['h']
            for s in scales:
                sw, sh = int(tw * s), int(th * s)
                if sw <= 4 or sh <= 4 or sw >= lw or sh >= lh:
                    continue
                
                scaled_tmpl = cv2.resize(tmpl['dist'], (sw, sh), interpolation=cv2.INTER_AREA)
                res = cv2.matchTemplate(line_dist, scaled_tmpl, cv2.TM_CCOEFF_NORMED)
                
                # Detectar solo picos locales estrictos (excluyendo regiones planas de papel)
                k_size = max(15, min(sw, sh) // 2 * 2 + 1)
                footprint = np.ones((k_size, k_size), dtype=bool)
                footprint[k_size // 2, k_size // 2] = False
                local_max = maximum_filter(res, footprint=footprint)
                
                peaks = (res > local_max) & (res >= threshold)
                
                ys, xs = np.where(peaks)
                for pt_y, pt_x in zip(ys, xs):
                    score = float(res[pt_y, pt_x])
                    all_boxes.append([int(pt_x), int(pt_y), sw, sh])
                    all_scores.append(score)
                    all_meta.append({
                        'template_idx': t_idx,
                        'template_type': tmpl['type'],
                        'scale': s
                    })

        # Non-Maximum Suppression
        keep_indices = non_max_suppression(all_boxes, all_scores, iou_thresh=0.35)
        
        final_matches = []
        for idx in keep_indices:
            b = all_boxes[idx]
            sc = all_scores[idx]
            meta = all_meta[idx]
            final_matches.append({
                'x': b[0],
                'y': b[1],
                'w': b[2],
                'h': b[3],
                'score': round(sc, 4),
                'template_type': meta['template_type'],
                'scale': meta['scale']
            })

        # Ordenar de izquierda a derecha en el renglón
        final_matches.sort(key=lambda m: m['x'])

        # Contar ocurrencias reales en Ground Truth si existe
        gt_file = os.path.join(EXP_03_DIR, "dataset_muestras_p02_p03.json")
        gt_count = None
        if os.path.exists(gt_file) and char_target:
            with open(gt_file, 'r', encoding='utf-8') as f:
                for row in json.load(f):
                    if row['id'] == line_id:
                        gt_count = row.get('ground_truth', row.get('text', '')).count(char_target)
                        break

        response = {
            'line_id': line_id,
            'glyph_id': glyph_id,
            'character': char_target,
            'threshold_used': threshold,
            'detected_count': len(final_matches),
            'gt_count': gt_count,
            'templates_count': len(templates),
            'matches': final_matches
        }
        self.send_bytes(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_learn_patches(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        payload = json.loads(body.decode('utf-8'))

        line_id = payload.get('line_id')
        glyph_id = payload.get('glyph_id')
        char_target = payload.get('character', '')
        clicks = payload.get('clicks', []) # list of {x, y, w, h} or {x, y}

        line_path = os.path.join(EXP_02_DIR, "crops", f"{line_id}.png")
        if not os.path.exists(line_path) or not clicks:
            self.send_bytes(json.dumps({'error': 'Parámetros inválidos'}).encode('utf-8'), status=400)
            return

        line_img = cv2.imread(line_path)
        lh, lw = line_img.shape[:2]

        memoria = load_memoria()
        if glyph_id not in memoria:
            memoria[glyph_id] = []

        new_patches_added = 0
        timestamp = int(time.time() * 1000)

        for i, clk in enumerate(clicks):
            x = int(clk.get('x', 0))
            y = int(clk.get('y', 0))
            w = int(clk.get('w', 30))
            h = int(clk.get('h', 40))

            # Si el clic es solo un punto, centrar la caja
            if 'w' not in clk or 'h' not in clk:
                w, h = 32, 45
                x = max(0, x - w // 2)
                y = max(0, y - h // 2)

            x = max(0, min(lw - 1, x))
            y = max(0, min(lh - 1, y))
            w = max(4, min(lw - x, w))
            h = max(4, min(lh - y, h))

            patch_crop = line_img[y:y+h, x:x+w]
            patch_fn = f"patch_{glyph_id}_{timestamp}_{i}.png"
            patch_fp = os.path.join(PATCHES_DIR, patch_fn)
            cv2.imwrite(patch_fp, patch_crop)

            memoria[glyph_id].append({
                'id': f"{glyph_id}_p{timestamp}_{i}",
                'filename': patch_fn,
                'line_id': line_id,
                'bbox': [x, y, w, h],
                'timestamp': timestamp
            })
            new_patches_added += 1

        save_memoria(memoria)

        response = {
            'success': True,
            'glyph_id': glyph_id,
            'new_patches_added': new_patches_added,
            'total_memory_patches': len(memoria[glyph_id])
        }
        self.send_bytes(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_reset_memory(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        payload = json.loads(body.decode('utf-8')) if length > 0 else {}

        gid = payload.get('glyph_id')
        memoria = load_memoria()

        if gid and gid in memoria:
            del memoria[gid]
        elif not gid:
            memoria = {}

        save_memoria(memoria)
        self.send_bytes(json.dumps({'success': True, 'memoria': memoria}).encode('utf-8'))

def run():
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(('127.0.0.1', PORT), SpotterHandler)
    print(f"\n[SERVER 05] Servidor de Spotting Interactivo iniciado en http://127.0.0.1:{PORT}\n", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.", flush=True)

if __name__ == '__main__':
    run()
