"""
Motor de Síntesis Caligráfica de Frases Cursivas (Francisco Coloane - Exp 07.1)
==============================================================================
Ensambla glifos del Exp 06 aplicando métricas de ligadura y curvatura Bézier
para generar frases sintéticas completas con apariencia manuscrita natural.
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

class ColoaneHandwritingSynthesizer:
    def __init__(self):
        self.glyphs_by_char = {}
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

        print(f"✓ Base de glifos cargada: {len(all_glyphs)} glifos ({len(self.glyphs_by_char)} caracteres únicos)")

    def get_best_glyph(self, char, position='media', sample_idx=None):
        """
        Selecciona el mejor glifo considerando la posición (inicial, media, final)
        y ofreciendo variabilidad natural si hay múltiples muestras.
        """
        candidates = self.glyphs_by_char.get(char, [])
        if not candidates:
            # Fallback para tildes o mayúsculas/minúsculas
            if char == 'á': candidates = self.glyphs_by_char.get('a', [])
            elif char == 'é': candidates = self.glyphs_by_char.get('e', [])
            elif char == 'í': candidates = self.glyphs_by_char.get('i', [])
            elif char == 'ó': candidates = self.glyphs_by_char.get('o', [])
            elif char == 'ú': candidates = self.glyphs_by_char.get('u', [])
            elif char.lower() in self.glyphs_by_char:
                candidates = self.glyphs_by_char.get(char.lower(), [])
            elif char.upper() in self.glyphs_by_char:
                candidates = self.glyphs_by_char.get(char.upper(), [])

        if not candidates:
            return None

        # Filtrar por posición deseada si es posible
        pos_candidates = [g for g in candidates if g.get('position') == position]
        if not pos_candidates:
            pos_candidates = candidates # Fallback a cualquier posición si no existe específica

        if sample_idx is not None and 0 <= sample_idx < len(pos_candidates):
            return pos_candidates[sample_idx]
        return random.choice(pos_candidates)

    def synthesize_phrase(self, text, paper_bg=True, draw_ligatures=True, jitter=True):
        """
        Ensambla la frase completa y dibuja los puentes de ligadura Bézier.
        """
        words = text.split(' ')
        
        # Calcular dimensiones del lienzo
        char_advance = 22.0  # Constante media descubierta en Exp 07 (20-24px)
        space_width = 38.0   # Separación entre palabras
        canvas_height = 140
        canvas_width = int(len(text) * char_advance + len(words) * space_width + 120)

        # Crear lienzo
        if paper_bg:
            # Color de papel libreta antiguo de Coloane (#f4ede2 con sutil grano)
            canvas = Image.new('RGBA', (canvas_width, canvas_height), (244, 237, 226, 255))
            draw = ImageDraw.Draw(canvas)
            # Textura de papel sutil
            noise = np.random.normal(0, 3, (canvas_height, canvas_width, 3)).astype(np.int16)
            base_arr = np.array(canvas.convert('RGB'), dtype=np.int16)
            noisy_arr = np.clip(base_arr + noise, 0, 255).astype(np.uint8)
            canvas = Image.fromarray(noisy_arr).convert('RGBA')
            draw = ImageDraw.Draw(canvas)
        else:
            canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(canvas)

        cursor_x = 40.0
        baseline_y = 75.0
        placed_glyphs = []

        ink_color = (25, 30, 45, 235) # Tinta azul oscuro/negra caligráfica

        for w_idx, word in enumerate(words):
            if not word:
                continue

            word_len = len(word)
            last_exit_point = None

            for i, char in enumerate(word):
                # Determinar posición caligráfica
                if i == 0 and word_len > 1:
                    pos = 'inicial'
                elif i == word_len - 1 and word_len > 1:
                    pos = 'final'
                elif word_len == 1:
                    pos = 'aislada'
                else:
                    pos = 'media'

                glyph = self.get_best_glyph(char, position=pos)
                if not glyph:
                    cursor_x += char_advance
                    continue

                crop_iso_file = os.path.join(CROPS_ISO_DIR, glyph.get('crop_isolated_file', ''))
                if not os.path.exists(crop_iso_file):
                    cursor_x += char_advance
                    continue

                glyph_img = Image.open(crop_iso_file).convert('RGBA')
                gw, gh = glyph_img.size

                # Ajustar baseline según proporciones del glifo
                # Glifos descendentes (p, g, y, j, q) se alinean más abajo
                # Glifos ascendentes (t, l, d, b, h) se alinean más arriba
                y_offset = -gh * 0.65
                if char in 'gyjpq':
                    y_offset = -gh * 0.40
                elif char in 'ldbhkft':
                    y_offset = -gh * 0.75
                elif char.isupper():
                    y_offset = -gh * 0.80

                # Jitter natural de la mano humana
                j_x = random.uniform(-1.0, 1.0) if jitter else 0.0
                j_y = random.uniform(-1.5, 1.5) if jitter else 0.0

                pos_x = int(cursor_x + j_x)
                pos_y = int(baseline_y + y_offset + j_y)

                # Colorear tinta del glifo al color de tinta manuscrita
                alpha = np.array(glyph_img)[:, :, 3]
                colored_glyph = Image.new('RGBA', (gw, gh), ink_color)
                colored_glyph.putalpha(Image.fromarray(alpha))

                # Estimar anclas de entrada y salida
                entry_point = (pos_x + int(gw * 0.15), pos_y + int(gh * 0.70))
                exit_point = (pos_x + int(gw * 0.85), pos_y + int(gh * 0.70))

                # Dibujar ligadura continua con la letra anterior dentro de la misma palabra
                if draw_ligatures and last_exit_point is not None:
                    # Curva Bézier C1 suave
                    p0 = np.array(last_exit_point, dtype=float)
                    p3 = np.array(entry_point, dtype=float)
                    
                    dx = p3[0] - p0[0]
                    p1 = p0 + np.array([dx * 0.4, -random.uniform(0, 3)])
                    p2 = p3 - np.array([dx * 0.4, -random.uniform(0, 3)])

                    bezier_pts = []
                    for t in np.linspace(0, 1, 15):
                        pt = (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3
                        bezier_pts.append((int(pt[0]), int(pt[1])))

                    for k in range(len(bezier_pts) - 1):
                        draw.line([bezier_pts[k], bezier_pts[k+1]], fill=ink_color, width=2)

                # Estampar glifo sobre el lienzo
                canvas.paste(colored_glyph, (pos_x, pos_y), colored_glyph)

                last_exit_point = exit_point
                cursor_x += max(14.0, gw * 0.60 + random.uniform(2, 6))

                placed_glyphs.append({
                    "char": char,
                    "glyph_id": glyph['id'],
                    "pos_x": pos_x,
                    "pos_y": pos_y,
                    "w": gw,
                    "h": gh
                })

            # Espacio entre palabras
            cursor_x += space_width + random.uniform(-2, 4)

        return canvas, placed_glyphs

def main():
    synthesizer = ColoaneHandwritingSynthesizer()
    target_phrase = "los reyes y aristóteles"

    print(f"\nSintetizando frase manuscrita: «{target_phrase}»...")
    
    # 1. Renderizar sobre papel antiguo
    img_paper, info = synthesizer.synthesize_phrase(target_phrase, paper_bg=True, draw_ligatures=True)
    out_paper = os.path.join(OUT_DIR, "frase_los_reyes_y_aristoteles.png")
    img_paper.save(out_paper, "PNG")
    print(f"✓ Guardado sobre papel: {out_paper}")

    # 2. Renderizar con fondo transparente RGBA
    img_trans, _ = synthesizer.synthesize_phrase(target_phrase, paper_bg=False, draw_ligatures=True)
    out_trans = os.path.join(OUT_DIR, "frase_los_reyes_y_aristoteles_transparente.png")
    img_trans.save(out_trans, "PNG")
    print(f"✓ Guardado transparente: {out_trans}")

if __name__ == '__main__':
    main()
