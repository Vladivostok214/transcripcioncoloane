"""
Motor de Síntesis Caligráfica de Frases Cursivas (Francisco Coloane - Exp 07.1)
==============================================================================
Ensambla glifos normalizados por x-height, alineación precisa de línea base,
recorte de márgenes transparentes (tight bounding box) y ligaduras Bézier C1.
"""

import os
import sys
import json
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXP06_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '06_web_coloane'))
EXP07_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '07_anotador_palabras_ligaduras'))

GLYPHS_DB_PATH = os.path.join(EXP06_DIR, 'dataset_glifos_manuales.json')
CROPS_ISO_DIR = os.path.join(EXP06_DIR, 'crops_isolated')
OUT_DIR = os.path.join(BASE_DIR, 'output')

os.makedirs(OUT_DIR, exist_ok=True)

# Categorías de letras según anatomía tipográfica
LOWER_X_HEIGHT_CHARS = set('acemnorsuvwxz')
ASCENDER_CHARS = set('bdfhklßt')
DESCENDER_CHARS = set('gjpqy')
UPPER_CHARS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ')

TARGET_X_HEIGHT = 28.0  # Altura estándar de una letra minúscula 'x' a 300 DPI
TARGET_ASCENDER_HEIGHT = 56.0 # Altura estándar de letras altas 'l', 'b', mayúsculas

class ColoaneHandwritingSynthesizer:
    def __init__(self):
        self.glyphs_by_char = {}
        self.glyph_cache = {}
        self.load_glyph_database()

    def load_glyph_database(self):
        if not os.path.exists(GLYPHS_DB_PATH):
            print(f"Error: No se encontró {GLYPHS_DB_PATH}")
            return

        with open(GLYPHS_DB_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        all_glyphs = data.get('glyphs', [])
        for g in all_glyphs:
            char = g['character']
            self.glyphs_by_char.setdefault(char, []).append(g)

        print(f"Base de glifos cargada: {len(all_glyphs)} glifos ({len(self.glyphs_by_char)} caracteres)")

    def get_processed_glyph(self, char, position='media', sample_idx=None):
        """
        Obtiene y preprocesa el glifo: recorta márgenes transparentes,
        normaliza la escala a la altura de x (x-height) y halla anclas reales.
        """
        # Normalizar tildes
        has_accent = False
        base_char = char
        if char in 'áàäâ': base_char = 'a'; has_accent = True
        elif char in 'éèëê': base_char = 'e'; has_accent = True
        elif char in 'íìïî': base_char = 'i'; has_accent = True
        elif char in 'óòöô': base_char = 'o'; has_accent = True
        elif char in 'úùüû': base_char = 'u'; has_accent = True

        candidates = self.glyphs_by_char.get(base_char, [])
        if not candidates and base_char.lower() in self.glyphs_by_char:
            candidates = self.glyphs_by_char[base_char.lower()]
        if not candidates and base_char.upper() in self.glyphs_by_char:
            candidates = self.glyphs_by_char[base_char.upper()]

        if not candidates:
            return None

        # Filtrar por posición si existe
        pos_matches = [g for g in candidates if g.get('position') == position]
        pool = pos_matches if pos_matches else candidates
        
        glyph_meta = pool[sample_idx % len(pool)] if sample_idx is not None else random.choice(pool)
        glyph_id = glyph_meta['id']

        if glyph_id in self.glyph_cache:
            res = self.glyph_cache[glyph_id]
            res_copy = dict(res)
            res_copy['has_accent'] = has_accent
            return res_copy

        crop_path = os.path.join(CROPS_ISO_DIR, glyph_meta['crop_isolated_file'])
        if not os.path.exists(crop_path):
            return None

        img = Image.open(crop_path).convert('RGBA')
        arr = np.array(img)
        alpha = arr[:, :, 3]

        non_zero = np.argwhere(alpha > 30)
        if len(non_zero) == 0:
            return None

        min_y, min_x = non_zero.min(axis=0)
        max_y, max_x = non_zero.max(axis=0)

        # Recorte ceñido a la tinta real (Tight crop)
        tight_alpha = alpha[min_y:max_y+1, min_x:max_x+1]
        tight_h, tight_w = tight_alpha.shape

        # Normalización de escala según anatomía
        if base_char in LOWER_X_HEIGHT_CHARS:
            scale = TARGET_X_HEIGHT / max(10.0, float(tight_h))
        elif base_char in ASCENDER_CHARS or base_char in UPPER_CHARS:
            scale = TARGET_ASCENDER_HEIGHT / max(20.0, float(tight_h))
        elif base_char in DESCENDER_CHARS:
            scale = 48.0 / max(20.0, float(tight_h))
        else:
            scale = TARGET_X_HEIGHT / max(10.0, float(tight_h))

        # Limitar escala extrema
        scale = max(0.25, min(1.8, scale))
        norm_w = max(4, int(round(tight_w * scale)))
        norm_h = max(4, int(round(tight_h * scale)))

        resized_alpha = np.array(Image.fromarray(tight_alpha).resize((norm_w, norm_h), Image.Resampling.BILINEAR))

        # Encontrar anclas reales de entrada (leftmost) y salida (rightmost)
        nz_scaled = np.argwhere(resized_alpha > 40)
        if len(nz_scaled) > 0:
            # Entrada: píxel más a la izquierda
            left_col = nz_scaled[:, 1].min()
            left_pixels = nz_scaled[nz_scaled[:, 1] == left_col]
            entry_y = int(np.mean(left_pixels[:, 0]))
            entry_pt = (0, entry_y)

            # Salida: píxel más a la derecha
            right_col = nz_scaled[:, 1].max()
            right_pixels = nz_scaled[nz_scaled[:, 1] == right_col]
            exit_y = int(np.mean(right_pixels[:, 0]))
            exit_pt = (norm_w - 1, exit_y)
        else:
            entry_pt = (0, norm_h // 2)
            exit_pt = (norm_w - 1, norm_h // 2)

        # Baseline offset relativo
        # En una letra 'x' o 'a', el fondo de la letra descansa sobre la baseline (y_rel = norm_h)
        if base_char in DESCENDER_CHARS:
            baseline_rel_y = int(norm_h * 0.45) # La mitad superior sobre la baseline, la cola cuelga
        elif base_char in ASCENDER_CHARS or base_char in UPPER_CHARS:
            baseline_rel_y = norm_h - 2 # Descansa sobre la baseline
        else:
            baseline_rel_y = norm_h - 1

        processed = {
            "glyph_id": glyph_id,
            "char": base_char,
            "has_accent": has_accent,
            "alpha": resized_alpha,
            "w": norm_w,
            "h": norm_h,
            "entry_pt": entry_pt,
            "exit_pt": exit_pt,
            "baseline_rel_y": baseline_rel_y
        }

        self.glyph_cache[glyph_id] = processed
        return dict(processed)

    def synthesize_phrase(self, text, paper_bg=True, draw_ligatures=True, jitter_amt=0.8):
        """
        Sintetiza la frase con alineación estricta de baseline y ligaduras Bézier C1.
        """
        words = text.split(' ')
        canvas_h = 160
        baseline_y = 90.0

        # Estimar ancho necesario
        approx_w = int(len(text) * 22 + len(words) * 35 + 160)
        canvas_w = max(700, approx_w)

        # Color de papel o transparente
        if paper_bg:
            canvas = Image.new('RGBA', (canvas_w, canvas_h), (244, 237, 226, 255))
            # Textura de papel
            noise = np.random.normal(0, 2.5, (canvas_h, canvas_w, 3)).astype(np.int16)
            base_arr = np.array(canvas.convert('RGB'), dtype=np.int16)
            noisy_arr = np.clip(base_arr + noise, 0, 255).astype(np.uint8)
            canvas = Image.fromarray(noisy_arr).convert('RGBA')
        else:
            canvas = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))

        draw = ImageDraw.Draw(canvas)
        ink_rgba = (24, 34, 52, 235) # Azul noche caligráfico de Coloane

        cursor_x = 45.0
        word_space = 36.0

        for w_idx, word in enumerate(words):
            if not word:
                continue

            word_len = len(word)
            last_exit_abs = None

            for i, char in enumerate(word):
                if i == 0 and word_len > 1: pos = 'inicial'
                elif i == word_len - 1 and word_len > 1: pos = 'final'
                elif word_len == 1: pos = 'aislada'
                else: pos = 'media'

                g = self.get_processed_glyph(char, position=pos)
                if not g:
                    cursor_x += 20.0
                    continue

                alpha = g['alpha']
                gw, gh = g['w'], g['h']

                # Calcular posición Y alineada exactamente a la línea base
                jy = random.uniform(-jitter_amt, jitter_amt)
                jx = random.uniform(-jitter_amt * 0.5, jitter_amt * 0.5)

                pos_x = int(round(cursor_x + jx))
                pos_y = int(round(baseline_y - g['baseline_rel_y'] + jy))

                entry_abs = (pos_x + g['entry_pt'][0], pos_y + g['entry_pt'][1])
                exit_abs = (pos_x + g['exit_pt'][0], pos_y + g['exit_pt'][1])

                # Dibujar ligadura Bézier con la letra previa
                if draw_ligatures and last_exit_abs is not None:
                    p0 = np.array(last_exit_abs, dtype=float)
                    p3 = np.array(entry_abs, dtype=float)

                    dx = p3[0] - p0[0]
                    # Control points para curva Bézier natural ascendente
                    p1 = p0 + np.array([dx * 0.45, 1.5])
                    p2 = p3 - np.array([dx * 0.45, 1.5])

                    bezier_pts = []
                    for t in np.linspace(0, 1, 16):
                        pt = (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3
                        bezier_pts.append((int(round(pt[0])), int(round(pt[1]))))

                    for k in range(len(bezier_pts) - 1):
                        draw.line([bezier_pts[k], bezier_pts[k+1]], fill=ink_rgba, width=2)

                # Estampar glifo teñido
                colored_glyph = Image.new('RGBA', (gw, gh), ink_rgba)
                colored_glyph.putalpha(Image.fromarray(alpha))
                canvas.paste(colored_glyph, (pos_x, pos_y), colored_glyph)

                # Si tiene tilde (ej. 'ó'), dibujar trazo de tilde
                if g.get('has_accent'):
                    accent_x0 = pos_x + int(gw * 0.3)
                    accent_y0 = pos_y - 8
                    accent_x1 = pos_x + int(gw * 0.7)
                    accent_y1 = pos_y - 14
                    draw.line([(accent_x0, accent_y0), (accent_x1, accent_y1)], fill=ink_rgba, width=2)

                last_exit_abs = exit_abs
                # Avance horizontal: ancho de la letra + pequeño puente inter-glifo
                cursor_x += gw + random.uniform(2, 6)

            cursor_x += word_space

        return canvas

def main():
    synthesizer = ColoaneHandwritingSynthesizer()
    target_phrase = "los reyes y aristóteles"

    print(f"\nSintetizando frase manuscrita con alineación x-height: «{target_phrase}»...")

    # 1. Sobre papel antiguo
    img_paper = synthesizer.synthesize_phrase(target_phrase, paper_bg=True, draw_ligatures=True)
    out_paper = os.path.join(OUT_DIR, "frase_los_reyes_y_aristoteles.png")
    img_paper.save(out_paper, "PNG")
    print(f"✓ Guardado papel: {out_paper}")

    # 2. Transparente
    img_trans = synthesizer.synthesize_phrase(target_phrase, paper_bg=False, draw_ligatures=True)
    out_trans = os.path.join(OUT_DIR, "frase_los_reyes_y_aristoteles_transparente.png")
    img_trans.save(out_trans, "PNG")
    print(f"✓ Guardado transparente: {out_trans}")

if __name__ == '__main__':
    main()
