import os
import sys
import json
import csv
import re
import argparse
import time
import cv2
import numpy as np
import xml.etree.ElementTree as ET
from svgpathtools import parse_path, Path
import vtracer

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def get_safe_char(char):
    """Returns safe ASCII representation for non-ASCII characters in filenames."""
    if not char:
        return "empty"
    safe = ""
    for c in char:
        if c.isalnum() and ord(c) < 128:
            safe += c
        else:
            safe += f"u{ord(c):04x}"
    return safe

class GlyphVectorizer:
    def __init__(self, exp04_dir=None, exp04_2_dir=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.exp04_dir = exp04_dir or os.path.join(base_dir, '04.1_abecedario_glifos_manual')
        self.exp04_2_dir = exp04_2_dir or os.path.join(base_dir, '04.2_vectorizacion_glifos')
        
        self.crops_dir = os.path.join(self.exp04_dir, 'crops')
        self.crops_iso_dir = os.path.join(self.exp04_dir, 'crops_isolated')
        self.db_manual_path = os.path.join(self.exp04_dir, 'dataset_glifos_manuales.json')
        
        self.svg_out_dir = os.path.join(self.exp04_2_dir, 'svg')
        self.db_vector_path = os.path.join(self.exp04_2_dir, 'dataset_glifos_vectoriales.json')
        self.csv_vector_path = os.path.join(self.exp04_2_dir, 'dataset_glifos_vectoriales.csv')
        
        os.makedirs(self.svg_out_dir, exist_ok=True)

    def load_manual_db(self):
        if not os.path.exists(self.db_manual_path):
            raise FileNotFoundError(f"No se encontró la base de datos manual en {self.db_manual_path}")
        with open(self.db_manual_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def preprocess_image(self, img_bgr, poly=None, bbox=None):
        """
        Aplica la receta ganadora de preprocesamiento:
        1. Máscara de polígono (si existe) para aislar la letra.
        2. CLAHE (3.0) para realzar contraste de tinta local.
        3. Filtro Bilateral para eliminar textura del papel.
        4. Umbralización Otsu.
        5. Despeckle (> 20px) y cierre morfológico 2x2.
        """
        h_orig, w_orig = img_bgr.shape[:2]

        # 1. Aplicar polígono si está presente
        if poly and len(poly) >= 3 and bbox:
            bx, by = bbox[0], bbox[1]
            local_pts = np.array([[int(p[0] - bx), int(p[1] - by)] for p in poly], dtype=np.int32)
            mask = np.zeros((h_orig, w_orig), dtype=np.uint8)
            cv2.fillPoly(mask, [local_pts], 255)
            bg = np.full_like(img_bgr, 255)
            img_bgr = np.where(mask[:, :, None] == 255, img_bgr, bg)

        # 2. Escala de grises y CLAHE adaptativo
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # 3. Filtro bilateral suave
        denoised = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)

        # 4. Otsu binarization
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 5. Despeckle adaptativo (preservar tildes y puntos > 12 px)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(255 - binary, connectivity=8)
        cleaned = np.zeros_like(binary)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= 12:
                cleaned[labels == i] = 255

        # 6. Cierre morfológico suave para conectar trazos finos
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

        # Invertir a tinta negra sobre fondo blanco para vtracer (resolución natural pura)
        vtracer_img = np.where(cleaned == 255, 0, 255).astype(np.uint8)
        return cv2.cvtColor(vtracer_img, cv2.COLOR_GRAY2BGR), cleaned

    def vectorize_single_glyph(self, glyph_data, force=False):
        glyph_id = glyph_data['id']
        char = glyph_data.get('character', '')
        cat = glyph_data.get('category', 'minuscula')
        
        svg_filename = f"{glyph_id}.svg"
        svg_filepath = os.path.join(self.svg_out_dir, svg_filename)

        if not force and os.path.exists(svg_filepath):
            try:
                tree = ET.parse(svg_filepath)
                return {
                    'status': 'skipped',
                    'glyph_id': glyph_id,
                    'svg_file': svg_filename,
                    'character': char,
                    'category': cat
                }
            except Exception:
                pass

        # Buscar imagen de entrada (priorizar RGB original, fallback a crops_isolated)
        crop_file = glyph_data.get('crop_file')
        crop_iso_file = glyph_data.get('crop_isolated_file')

        img_path = None
        if crop_file and os.path.exists(os.path.join(self.crops_dir, crop_file)):
            img_path = os.path.join(self.crops_dir, crop_file)
        elif crop_iso_file and os.path.exists(os.path.join(self.crops_iso_dir, crop_iso_file)):
            img_path = os.path.join(self.crops_iso_dir, crop_iso_file)

        if not img_path:
            return {'status': 'error', 'glyph_id': glyph_id, 'error': f'Crop no encontrado: {crop_file}'}

        img_bgr = cv2.imread(img_path)
        if img_bgr is None:
            return {'status': 'error', 'glyph_id': glyph_id, 'error': f'Error al leer imagen: {img_path}'}

        h_orig, w_orig = img_bgr.shape[:2]
        poly = glyph_data.get('polygon')
        bbox = glyph_data.get('bbox')

        # Preprocesamiento a resolución natural (sin interpolación destructiva)
        vtracer_input, cleaned_mask = self.preprocess_image(img_bgr, poly, bbox)

        # Archivos temporales para vtracer
        temp_in = os.path.join(self.svg_out_dir, f"temp_{glyph_id}_in.png")
        temp_out = os.path.join(self.svg_out_dir, f"temp_{glyph_id}_out.svg")
        cv2.imwrite(temp_in, vtracer_input)

        try:
            vtracer.convert_image_to_svg_py(
                temp_in,
                temp_out,
                colormode='binary',
                filter_speckle=6,
                corner_threshold=60,
                length_threshold=4.0,
                splice_threshold=45,
                path_precision=2
            )

            # Parsear SVG con svgpathtools y XML
            tree = ET.parse(temp_out)
            root = tree.getroot()

            combined_path = Path()
            for p_elem in root.findall('.//{http://www.w3.org/2000/svg}path'):
                d = p_elem.get('d')
                tr = p_elem.get('transform', '')
                tx, ty = 0.0, 0.0
                if 'translate' in tr:
                    m = re.search(r'translate\(([^,]+),\s*([^)]+)\)', tr)
                    if m:
                        tx = float(m.group(1))
                        ty = float(m.group(2))
                if d:
                    subpath = parse_path(d).translated(complex(tx, ty))
                    combined_path.extend(subpath)

            node_count = len(combined_path)
            subpaths_count = len(list(combined_path.continuous_subpaths()))

            if node_count == 0:
                # SVG vacío
                norm_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="100%" height="100%"></svg>'
                metrics = {"scale": 1.0, "tx": 0.0, "ty": 0.0, "baseline": 750}
            else:
                xmin, xmax, ymin, ymax = combined_path.bbox()
                pw = max(xmax - xmin, 1.0)
                ph = max(ymax - ymin, 1.0)

                # Definir altura objetivo según categoría tipográfica
                if cat in ['mayuscula', 'ascendente']:
                    target_h = 700.0
                elif cat == 'descendente':
                    target_h = 660.0
                elif cat in ['numero', 'signo']:
                    target_h = 650.0
                else:
                    # Minúscula estándar
                    target_h = 600.0

                scale = target_h / ph
                # Limitar ancho para evitar desbordes horizontales
                if pw * scale > 820.0:
                    scale = 820.0 / pw

                scaled_w = pw * scale
                offset_x = (1000.0 - scaled_w) / 2.0 - (xmin * scale)

                # Posicionamiento de Baseline (y = 750)
                if cat == 'descendente':
                    offset_y = 520.0 - (ymin * scale)
                else:
                    offset_y = 750.0 - (ymax * scale)

                d_str = combined_path.d()
                norm_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="100%" height="100%">
  <!-- Glyph ID: {glyph_id} | Char: {char} | Category: {cat} | Nodes: {node_count} -->
  <g id="glyph" fill="#111827" stroke="none" transform="translate({offset_x:.2f}, {offset_y:.2f}) scale({scale:.4f})">
    <path d="{d_str}" fill-rule="evenodd" />
  </g>
</svg>'''
                metrics = {
                    "viewBox": "0 0 1000 1000",
                    "scale": round(scale, 4),
                    "tx": round(offset_x, 2),
                    "ty": round(offset_y, 2),
                    "baseline": 750 if cat != 'descendente' else 520,
                    "bbox_vector": [round(xmin, 2), round(ymin, 2), round(pw, 2), round(ph, 2)]
                }

            with open(svg_filepath, 'w', encoding='utf-8') as f:
                f.write(norm_svg)

            return {
                'status': 'success',
                'glyph_id': glyph_id,
                'character': char,
                'category': cat,
                'notes': glyph_data.get('notes', ''),
                'svg_file': svg_filename,
                'node_count': node_count,
                'subpaths_count': subpaths_count,
                'orig_dimensions': [w_orig, h_orig],
                'metrics': metrics
            }

        finally:
            if os.path.exists(temp_in): os.remove(temp_in)
            if os.path.exists(temp_out): os.remove(temp_out)

    def process_all(self, force=False, target_char=None, target_id=None):
        manual_db = self.load_manual_db()
        glyphs = manual_db.get('glyphs', [])
        
        print(f"\n🚀 Iniciando Pipeline de Vectorización (Experimento 04.2)")
        print(f"📊 Total de glifos en base de datos manual: {len(glyphs)}")
        
        if target_char:
            glyphs = [g for g in glyphs if g.get('character') == target_char]
            print(f"🎯 Filtrado por carácter '{target_char}': {len(glyphs)} glifos")
        elif target_id:
            glyphs = [g for g in glyphs if g.get('id') == target_id]
            print(f"🎯 Filtrado por ID '{target_id}': {len(glyphs)} glifos")

        results = []
        stats = {'success': 0, 'skipped': 0, 'error': 0}
        start_time = time.time()

        for idx, g in enumerate(glyphs, 1):
            res = self.vectorize_single_glyph(g, force=force)
            results.append(res)
            st = res.get('status')
            stats[st] = stats.get(st, 0) + 1
            
            # Progress indicator
            c = g.get('character', '?')
            gid = g.get('id', '')
            nodes = res.get('node_count', 0)
            status_icon = "✓" if st == 'success' else ("↷" if st == 'skipped' else "✗")
            print(f"[{idx:3d}/{len(glyphs):3d}] {status_icon} '{c}' ({gid}) -> {nodes} nodos Bézier ({st})")

        elapsed = time.time() - start_time
        print(f"\n✨ Vectorización finalizada en {elapsed:.2f}s")
        print(f"   ✓ Exitosos: {stats['success']} | ↷ Omitidos (ya existían): {stats['skipped']} | ✗ Errores: {stats['error']}")

        # Guardar dataset_glifos_vectoriales.json
        vector_db = {
            'total_glyphs': len(results),
            'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'stats': stats,
            'glyphs': results
        }
        with open(self.db_vector_path, 'w', encoding='utf-8') as f:
            json.dump(vector_db, f, indent=2, ensure_ascii=False)
        print(f"📁 Base de datos vectorial guardada: {self.db_vector_path}")

        # Guardar CSV
        self.export_csv(results)
        print(f"📊 CSV vectorial guardado: {self.csv_vector_path}")
        return vector_db

    def export_csv(self, results):
        with open(self.csv_vector_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'character', 'category', 'svg_file', 'node_count', 'subpaths_count', 'status', 'orig_w', 'orig_h', 'scale', 'baseline'])
            for r in results:
                m = r.get('metrics', {})
                orig_dim = r.get('orig_dimensions', [0, 0])
                writer.writerow([
                    r.get('glyph_id', ''),
                    r.get('character', ''),
                    r.get('category', ''),
                    r.get('svg_file', ''),
                    r.get('node_count', 0),
                    r.get('subpaths_count', 0),
                    r.get('status', ''),
                    orig_dim[0] if orig_dim else 0,
                    orig_dim[1] if orig_dim else 0,
                    m.get('scale', 1.0),
                    m.get('baseline', 750)
                ])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Pipeline General de Vectorización de Glifos Caligráficos")
    parser.add_argument('--force', action='store_true', help="Regenerar todos los SVGs aunque ya existan")
    parser.add_argument('--char', type=str, default=None, help="Procesar solo muestras de un carácter específico")
    parser.add_argument('--id', type=str, default=None, help="Procesar un glifo específico por su ID")
    
    args = parser.parse_args()
    
    vectorizer = GlyphVectorizer()
    vectorizer.process_all(force=args.force, target_char=args.char, target_id=args.id)
