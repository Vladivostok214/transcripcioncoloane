import os
import sys
import json
import traceback
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PORT = 8002
BASE_DIR = r"C:\Users\WLADI\Desktop\COLOANE\TRANSCRIPCIONES COLOANE"
EXP_04_1_DIR = os.path.join(BASE_DIR, "experimentos", "06_web_coloane")
EXP_04_2_DIR = os.path.join(BASE_DIR, "experimentos", "04.2_vectorizacion_glifos")

CROPS_DIR = os.path.join(EXP_04_1_DIR, "crops")
CROPS_ISO_DIR = os.path.join(EXP_04_1_DIR, "crops_isolated")
SVG_DIR = os.path.join(EXP_04_2_DIR, "svg")
DB_MANUAL = os.path.join(EXP_04_1_DIR, "dataset_glifos_manuales.json")
DB_VECTOR = os.path.join(EXP_04_2_DIR, "dataset_glifos_vectoriales.json")
EVAL_FILE = os.path.join(EXP_04_2_DIR, "evaluacion_glifos.json")
HTML_FILE = os.path.join(EXP_04_2_DIR, "evaluador_interactivo.html")

class EvaluatorHandler(BaseHTTPRequestHandler):
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

            if path in ['/', '/index.html', '/evaluador.html']:
                if os.path.exists(HTML_FILE):
                    with open(HTML_FILE, 'rb') as f:
                        self.send_bytes(f.read(), 'text/html; charset=utf-8')
                else:
                    self.send_error(404, "evaluador_interactivo.html not found")

            elif path == '/api/dataset':
                self.handle_get_dataset()

            elif path.startswith('/crops/'):
                filename = os.path.basename(path)
                fp = os.path.join(CROPS_DIR, filename)
                if os.path.exists(fp):
                    with open(fp, 'rb') as f:
                        self.send_bytes(f.read(), 'image/png')
                else:
                    self.send_error(404, f"Crop not found: {filename}")

            elif path.startswith('/crops_isolated/'):
                filename = os.path.basename(path)
                fp = os.path.join(CROPS_ISO_DIR, filename)
                if os.path.exists(fp):
                    with open(fp, 'rb') as f:
                        self.send_bytes(f.read(), 'image/png')
                else:
                    self.send_error(404, f"Isolated crop not found: {filename}")

            elif path.startswith('/svg/'):
                filename = os.path.basename(path)
                fp = os.path.join(SVG_DIR, filename)
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
            if parsed.path == '/api/save_evaluation':
                self.handle_save_evaluation()
            else:
                self.send_error(404, "Endpoint no encontrado")
        except Exception:
            traceback.print_exc()

    def handle_get_dataset(self):
        manual_glyphs = {}
        if os.path.exists(DB_MANUAL):
            with open(DB_MANUAL, 'r', encoding='utf-8') as f:
                for g in json.load(f).get('glyphs', []):
                    manual_glyphs[g['id']] = g

        vector_glyphs = {}
        if os.path.exists(DB_VECTOR):
            with open(DB_VECTOR, 'r', encoding='utf-8') as f:
                for g in json.load(f).get('glyphs', []):
                    vector_glyphs[g.get('glyph_id', g.get('id'))] = g

        evaluations = {}
        if os.path.exists(EVAL_FILE):
            with open(EVAL_FILE, 'r', encoding='utf-8') as f:
                evaluations = json.load(f).get('evaluations', {})

        combined = []
        for gid, mg in manual_glyphs.items():
            vg = vector_glyphs.get(gid, {})
            ev = evaluations.get(gid, {'status': 'pending', 'notes': '', 'timestamp': None})
            
            svg_file = f"{gid}.svg"
            svg_path = os.path.join(SVG_DIR, svg_file)
            svg_exists = os.path.exists(svg_path)
            
            svg_content = ""
            if svg_exists:
                try:
                    with open(svg_path, 'r', encoding='utf-8') as sf:
                        svg_content = sf.read()
                except Exception:
                    pass

            combined.append({
                'id': gid,
                'character': mg.get('character', '?'),
                'category': mg.get('category', 'minuscula'),
                'line_id': mg.get('line_id', ''),
                'page': mg.get('page', ''),
                'notes': mg.get('notes', ''),
                'bbox': mg.get('bbox', [0, 0, 0, 0]),
                'crop_file': mg.get('crop_file', ''),
                'crop_isolated_file': mg.get('crop_isolated_file', ''),
                'svg_file': svg_file,
                'svg_exists': svg_exists,
                'svg_content': svg_content,
                'node_count': vg.get('node_count', 0),
                'evaluation': ev
            })

        response = {
            'total': len(combined),
            'stats': {
                'approved': sum(1 for g in combined if g['evaluation'].get('status') == 'approved'),
                'tweaks': sum(1 for g in combined if g['evaluation'].get('status') in ['tweaks', 'warning']),
                'rejected': sum(1 for g in combined if g['evaluation'].get('status') == 'rejected'),
                'pending': sum(1 for g in combined if g['evaluation'].get('status') == 'pending')
            },
            'glyphs': combined
        }
        self.send_bytes(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_save_evaluation(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        payload = json.loads(body.decode('utf-8'))

        gid = payload.get('glyph_id')
        status = payload.get('status')
        notes = payload.get('notes', '')

        evaluations = {}
        if os.path.exists(EVAL_FILE):
            with open(EVAL_FILE, 'r', encoding='utf-8') as f:
                evaluations = json.load(f).get('evaluations', {})

        import datetime
        evaluations[gid] = {
            'status': status,
            'notes': notes,
            'timestamp': datetime.datetime.now().isoformat()
        }

        with open(EVAL_FILE, 'w', encoding='utf-8') as f:
            json.dump({'evaluations': evaluations}, f, indent=2, ensure_ascii=False)

        stats = {
            'approved': sum(1 for e in evaluations.values() if e.get('status') == 'approved'),
            'tweaks': sum(1 for e in evaluations.values() if e.get('status') in ['tweaks', 'warning']),
            'rejected': sum(1 for e in evaluations.values() if e.get('status') == 'rejected'),
            'pending': sum(1 for e in evaluations.values() if e.get('status') == 'pending')
        }

        self.send_bytes(json.dumps({'success': True, 'glyph_id': gid, 'status': status, 'stats': stats}).encode('utf-8'))

def run():
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(('127.0.0.1', PORT), EvaluatorHandler)
    print(f"\n[SERVER] Servidor de Evaluacion iniciado en http://127.0.0.1:{PORT}\n", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.", flush=True)

if __name__ == '__main__':
    run()
