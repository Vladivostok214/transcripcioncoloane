"""
Servidor Local para el Experimento 07.1: Sintetizador de Frases Cursivas (Coloane)
==================================================================================
Puerto: 8086
Proporciona una interfaz web interactiva para componer cualquier texto en tiempo real
con la caligrafía continua de Francisco Coloane.
"""

import http.server
import socketserver
import os
import json
import base64
import sys
from urllib.parse import urlparse

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PORT = 8086
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXP06_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '06_web_coloane'))
EXP07_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '07_anotador_palabras_ligaduras'))

EXP04_2_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '04.2_vectorizacion_glifos'))

class SynthesizerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        import urllib.parse
        parsed = urlparse(self.path)
        clean_path = urllib.parse.unquote(parsed.path)

        if clean_path == '/' or clean_path == '/index.html':
            self.path = '/index.html'
            return super().do_GET()
        elif clean_path == '/api/init_glyphs':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            db_path = os.path.join(EXP06_DIR, 'dataset_glifos_manuales.json')
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"glyphs": []}).encode('utf-8'))
            return
        elif clean_path == '/api/init_vector_glyphs':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            db_path = os.path.join(EXP04_2_DIR, 'dataset_glifos_vectoriales.json')
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"glyphs": []}).encode('utf-8'))
            return
        elif clean_path == '/api/init_words':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            db_path = os.path.join(EXP07_DIR, 'dataset_palabras_manuales.json')
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"words": []}).encode('utf-8'))
            return
        elif clean_path.startswith('/svg/'):
            # Servir glifos vectoriales SVG desde Exp 04.2
            file_name = clean_path.replace('/svg/', '')
            target = os.path.join(EXP04_2_DIR, 'svg', file_name)
            if os.path.exists(target):
                self.send_response(200)
                self.send_header('Content-Type', 'image/svg+xml')
                self.end_headers()
                with open(target, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                return
        elif clean_path.startswith('/crops_isolated/'):
            # Servir directamente desde Exp 06
            file_name = clean_path.replace('/crops_isolated/', '')
            target = os.path.join(EXP06_DIR, 'crops_isolated', file_name)
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
        elif clean_path.startswith('/crops_palabras_isolated/'):
            # Servir desde Exp 07
            file_name = clean_path.replace('/crops_palabras_isolated/', '')
            target = os.path.join(EXP07_DIR, 'crops_palabras_isolated', file_name)
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
        elif parsed.path.startswith('/output/'):
            return super().do_GET()
        else:
            return super().do_GET()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), SynthesizerHandler) as httpd:
            print("="*65)
            print(f"  🖋️ SINTETIZADOR DE FRASES CURSIVAS (EXP 07.1) INICIADO")
            print(f"  👉 Abre en tu navegador: http://localhost:{PORT}")
            print("="*65)
            httpd.serve_forever()
    except OSError:
        alt_port = PORT + 1
        with socketserver.TCPServer(("", alt_port), SynthesizerHandler) as httpd:
            print("="*65)
            print(f"  🖋️ SINTETIZADOR DE FRASES (EXP 07.1) INICIADO (Puerto alternativo)")
            print(f"  👉 Abre en tu navegador: http://localhost:{alt_port}")
            print("="*65)
            httpd.serve_forever()

if __name__ == '__main__':
    run_server()
