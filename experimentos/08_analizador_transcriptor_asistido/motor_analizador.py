"""
Motor de Análisis y Transcripción Caligráfica Asistida (Exp 08 - Francisco Coloane)
==================================================================================
Integra:
1. Preprocesamiento y aislamiento de tinta (CLAHE + Bilateral + Otsu + Despeckle).
2. Segmentación de ligaduras por valles de densidad vertical (Métricas Exp 07).
3. Cotejo morfológico y topológico contra el catálogo de 114 glifos (Exp 06 / Exp 04.2).
4. Decodificador contextual guiado por el léxico literario de Francisco Coloane.
5. Generación de capas de diagnóstico visual para la interfaz web.
"""

import os
import sys
import json
import csv
import math
import cv2
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
EXP04_2_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '04.2_vectorizacion_glifos'))
CORPUS_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'corpus_coloane_obsidian', '03_analisis_lexico'))

OUT_DIR = os.path.join(BASE_DIR, 'output_analisis')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
DB_APROBADAS_JSON = os.path.join(BASE_DIR, 'dataset_transcripciones_aprobadas.json')
DB_APROBADAS_CSV = os.path.join(BASE_DIR, 'dataset_transcripciones_aprobadas.csv')

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

TARGET_X_HEIGHT = 28.0

class ColoaneManuscriptAnalyzer:
    def __init__(self):
        self.glyphs_db = []
        self.glyphs_by_char = {}
        self.glyph_templates = {}
        self.lexicon = {}
        self.bigrams = {}

        self.load_all_knowledge_bases()

    def load_all_knowledge_bases(self):
        # 1. Cargar Base de Glifos Manuales (Exp 06)
        path_g = os.path.join(EXP06_DIR, 'dataset_glifos_manuales.json')
        if os.path.exists(path_g):
            with open(path_g, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.glyphs_db = data.get('glyphs', [])
                for g in self.glyphs_db:
                    c = g['character']
                    self.glyphs_by_char.setdefault(c, []).append(g)

        # 2. Cargar y Preprocesar Plantillas de Glifos
        self.prepare_glyph_templates()

        # 3. Cargar Léxico y Frecuencias de Coloane (Corpus Obsidian)
        path_lex = os.path.join(CORPUS_DIR, 'coloane_lexicon_frecuencias.json')
        if os.path.exists(path_lex):
            with open(path_lex, 'r', encoding='utf-8') as f:
                self.lexicon = json.load(f)

        path_bi = os.path.join(CORPUS_DIR, 'coloane_bigramas_frecuentes.json')
        if os.path.exists(path_bi):
            with open(path_bi, 'r', encoding='utf-8') as f:
                self.bigrams = json.load(f)

        print(f"✓ Cerebro Cargado: {len(self.glyphs_db)} glifos | {len(self.lexicon)} palabras del léxico Coloane")

    def prepare_glyph_templates(self):
        """Preprocesa y normaliza cada glifo del catálogo para cotejo morfológico rápido."""
        crops_iso_dir = os.path.join(EXP06_DIR, 'crops_isolated')
        for g in self.glyphs_db:
            gid = g['id']
            char = g['character']
            fname = g.get('crop_isolated_file')
            if not fname:
                continue

            p = os.path.join(crops_iso_dir, fname)
            if not os.path.exists(p):
                continue

            img = cv2.imread(p, cv2.IMREAD_UNCHANGED)
            if img is None:
                continue

            # Extraer máscara binaria de tinta
            if img.shape[2] == 4:
                alpha = img[:, :, 3]
                mask = (alpha > 40).astype(np.uint8) * 255
            else:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

            # Tight Bounding Box
            pts = cv2.findNonZero(mask)
            if pts is None:
                continue
            x, y, w, h = cv2.boundingRect(pts)
            tight_mask = mask[y:y+h, x:x+w]

            # Normalizar tamaño estándar (28x28 para cotejo)
            resized = cv2.resize(tight_mask, (28, 28), interpolation=cv2.INTER_AREA)
            _, bin_norm = cv2.threshold(resized, 100, 255, cv2.THRESH_BINARY)

            # Calcular Momentos de Hu para invariancia de forma
            moments = cv2.HuMoments(cv2.moments(bin_norm)).flatten()
            log_hu = -np.sign(moments) * np.log10(np.abs(moments) + 1e-10)

            self.glyph_templates[gid] = {
                "id": gid,
                "character": char,
                "position": g.get('position', 'media'),
                "binary": bin_norm,
                "hu_moments": log_hu,
                "aspect_ratio": float(w) / max(1.0, float(h))
            }

    # =========================================================================
    # ETAPA 1: PREPROCESAMIENTO Y AISLAMIENTO DE TINTA
    # =========================================================================
    def preprocess_image(self, bgr_img):
        """Elimina textura de papel, compensa iluminación y extrae tinta pura."""
        h, w = bgr_img.shape[:2]
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

        # CLAHE adaptativo para contraste local de tinta
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Filtro bilateral para preservar bordes del trazo y suavizar papel
        denoised = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)

        # Binarización Otsu
        _, binary_inv = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Despeckle: eliminar partículas sueltas menores a 10px
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_inv, connectivity=8)
        clean_ink = np.zeros_like(binary_inv)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= 8:
                clean_ink[labels == i] = 255

        # Cierre morfológico suave para unificar trazos finos
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        clean_ink = cv2.morphologyEx(clean_ink, cv2.MORPH_CLOSE, kernel)

        return clean_ink

    # =========================================================================
    # ETAPA 2: SEGMENTACIÓN DE LIGADURAS Y VALLES DE DENSIDAD
    # =========================================================================
    def segment_words_and_characters(self, ink_mask):
        """
        Detecta palabras por vacíos horizontales y segmenta letras dentro
        de cada palabra usando el perfil de valles de densidad vertical.
        """
        h, w = ink_mask.shape
        proj_x = np.sum(ink_mask > 0, axis=0)

        # 1. Encontrar palabras (zonas continuas de tinta separadas por huecos > 18px)
        words_ranges = []
        in_word = False
        start_x = 0
        gap_count = 0

        for x in range(w):
            val = proj_x[x]
            if val > 0:
                if not in_word:
                    in_word = True
                    start_x = x
                gap_count = 0
            else:
                if in_word:
                    gap_count += 1
                    if gap_count > 16 or x == w - 1:
                        end_x = x - gap_count
                        if end_x - start_x > 8:
                            words_ranges.append((start_x, end_x))
                        in_word = False
                        gap_count = 0

        if in_word and (w - start_x > 8):
            words_ranges.append((start_x, w - 1))

        if not words_ranges:
            words_ranges = [(0, w - 1)]

        # 2. Para cada palabra, segmentar letras usando la constante de avance de Coloane (~20.3px)
        # y los mínimos locales del perfil vertical
        segmented_words = []
        for (wx0, wx1) in words_ranges:
            word_w = wx1 - wx0 + 1
            word_ink = ink_mask[:, wx0:wx1+1]
            word_proj = proj_x[wx0:wx1+1]

            # Estimar número de letras según la constante empírica de Coloane (20px/letra)
            est_chars = max(1, int(round(word_w / 20.3)))

            # Buscar valles de densidad dentro de la palabra
            valleys = []
            smoothed_proj = np.convolve(word_proj, np.ones(5)/5, mode='same')

            for x in range(6, word_w - 6):
                if smoothed_proj[x] < smoothed_proj[x-1] and smoothed_proj[x] < smoothed_proj[x+1]:
                    valleys.append(x)

            # Filtrar cortes candidatos respetando el espaciado mínimo de 12px
            cuts = [0]
            for v in valleys:
                if v - cuts[-1] >= 14:
                    cuts.append(v)
            if word_w - cuts[-1] < 12 and len(cuts) > 1:
                cuts.pop()
            cuts.append(word_w)

            # Generar segmentos de letras
            char_segments = []
            for i in range(len(cuts) - 1):
                cx0 = wx0 + cuts[i]
                cx1 = wx0 + cuts[i+1]
                char_ink = ink_mask[:, cx0:cx1]
                
                # Bounding box ceñido
                nz = cv2.findNonZero(char_ink)
                if nz is not None:
                    bx, by, bw, bh = cv2.boundingRect(nz)
                    char_segments.append({
                        "global_bbox": [cx0 + bx, by, bw, bh],
                        "rel_bbox": [cuts[i] + bx, by, bw, bh],
                        "sub_mask": char_ink[by:by+bh, bx:bx+bw],
                        "is_initial": (i == 0),
                        "is_final": (i == len(cuts) - 2)
                    })

            segmented_words.append({
                "word_bbox": [wx0, 0, word_w, h],
                "char_segments": char_segments
            })

        return segmented_words

    # =========================================================================
    # ETAPA 3: COTEJO MORFOLÓGICO CONTRA CATÁLOGO DE 114 GLIFOS
    # =========================================================================
    def match_character_segment(self, char_mask, is_initial=False, is_final=False):
        """
        Compara un segmento desconocido contra las 114 variantes del catálogo
        combinando similitud de forma Hu, IoU de solapamiento y proporciones.
        """
        if char_mask is None or char_mask.size == 0:
            return [("?", 0.0, "none")]

        h, w = char_mask.shape
        resized = cv2.resize(char_mask, (28, 28), interpolation=cv2.INTER_AREA)
        _, bin_norm = cv2.threshold(resized, 100, 255, cv2.THRESH_BINARY)

        # Momentos Hu de la muestra desconocida
        moments = cv2.HuMoments(cv2.moments(bin_norm)).flatten()
        log_hu = -np.sign(moments) * np.log10(np.abs(moments) + 1e-10)
        aspect_ratio = float(w) / max(1.0, float(h))

        candidates_scores = {}

        for gid, tmpl in self.glyph_templates.items():
            char = tmpl['character']

            # 1. Distancia de Momentos Hu
            hu_dist = np.linalg.norm(log_hu[:4] - tmpl['hu_moments'][:4])
            hu_score = np.exp(-hu_dist * 0.4)

            # 2. IoU (Intersection over Union) directo sobre máscara 28x28 normalizada
            intersection = np.logical_and(bin_norm > 0, tmpl['binary'] > 0).sum()
            union = np.logical_or(bin_norm > 0, tmpl['binary'] > 0).sum()
            iou_score = float(intersection) / max(1.0, float(union))

            # 3. Penalización por aspect ratio
            ar_diff = abs(aspect_ratio - tmpl['aspect_ratio'])
            ar_score = np.exp(-ar_diff * 1.2)

            # 4. Bonificación de posición caligráfica
            pos_bonus = 1.0
            if is_initial and tmpl['position'] == 'inicial': pos_bonus = 1.15
            elif is_final and tmpl['position'] == 'final': pos_bonus = 1.15
            elif (not is_initial and not is_final) and tmpl['position'] == 'media': pos_bonus = 1.05

            total_score = (iou_score * 0.50 + hu_score * 0.35 + ar_score * 0.15) * pos_bonus

            if char not in candidates_scores or total_score > candidates_scores[char]['score']:
                candidates_scores[char] = {
                    "score": total_score,
                    "matched_id": gid,
                    "character": char
                }

        # Ordenar por puntaje
        sorted_matches = sorted(candidates_scores.values(), key=lambda x: x['score'], reverse=True)
        top_matches = [(m['character'], round(float(m['score']), 3), m['matched_id']) for m in sorted_matches[:5]]
        return top_matches if top_matches else [("?", 0.0, "none")]

    # =========================================================================
    # ETAPA 4: DECODIFICADOR CONTEXTUAL CON EL LÉXICO DE COLOANE
    # =========================================================================
    def decode_word_with_coloane_context(self, char_predictions):
        """
        Toma las listas de candidatos por carácter y aplica el modelo de lenguaje
        del corpus de Coloane para resolver ambigüedades.
        """
        raw_word = "".join([preds[0][0] for preds in char_predictions])
        
        # Si la palabra cruda existe con alta frecuencia en el léxico de Coloane
        lower_raw = raw_word.lower()
        if lower_raw in self.lexicon:
            freq = self.lexicon[lower_raw]
            conf = min(0.99, np.mean([p[0][1] for p in char_predictions]) * 1.1)
            return raw_word, conf, [raw_word]

        # Búsqueda de candidatos similares en el léxico (Distancia Levenshtein + Puntuación Visual)
        word_candidates = []
        for vocab_word, freq in self.lexicon.items():
            if abs(len(vocab_word) - len(raw_word)) <= 1:
                # Calcular similitud simple
                match_count = sum(1 for a, b in zip(lower_raw, vocab_word) if a == b)
                sim_ratio = match_count / max(len(lower_raw), len(vocab_word))
                if sim_ratio >= 0.55:
                    score = sim_ratio * 0.65 + min(1.0, math.log10(freq + 1) / 4.0) * 0.35
                    word_candidates.append((vocab_word, score))

        word_candidates.sort(key=lambda x: x[1], reverse=True)
        top_words = [w[0] for w in word_candidates[:3]]

        if top_words and word_candidates[0][1] > 0.70:
            best_word = top_words[0]
            # Preservar mayúscula si la original lo era
            if raw_word and raw_word[0].isupper():
                best_word = best_word.capitalize()
            return best_word, round(word_candidates[0][1], 3), top_words

        return raw_word, round(np.mean([p[0][1] for p in char_predictions]), 3), top_words

    # =========================================================================
    # PIPELINE COMPLETO Y GENERACIÓN DE CAPAS DE DIAGNÓSTICO
    # =========================================================================
    def analyze_manuscript_image(self, image_path, session_id=None):
        """
        Ejecuta el pipeline completo de 4 etapas sobre la imagen provista
        y genera las capas de diagnóstico visual.
        """
        session_id = session_id or str(int(os.path.getmtime(image_path) * 1000) if os.path.exists(image_path) else 1000)
        
        bgr = cv2.imread(image_path)
        if bgr is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen: {image_path}")

        h, w = bgr.shape[:2]

        # 1. Aislamiento de Tinta
        clean_ink = self.preprocess_image(bgr)

        # 2. Segmentación de Palabras y Letras
        segmented_words = self.segment_words_and_characters(clean_ink)

        # 3. Cotejo de Glifos y Decodificación Contextual
        transcription_words = []
        analyzed_chars = []

        # Crear lienzos de capas de diagnóstico
        diag_bboxes = bgr.copy()
        diag_skeleton = np.zeros((h, w, 3), dtype=np.uint8)

        for w_idx, s_word in enumerate(segmented_words):
            char_preds_list = []
            for c_idx, s_char in enumerate(s_word['char_segments']):
                preds = self.match_character_segment(
                    s_char['sub_mask'],
                    is_initial=s_char['is_initial'],
                    is_final=s_char['is_final']
                )
                char_preds_list.append(preds)
                top_char, conf, gid = preds[0]

                gx, gy, gw, gh = s_char['global_bbox']
                analyzed_chars.append({
                    "char": top_char,
                    "confidence": conf,
                    "matched_glyph_id": gid,
                    "bbox": [gx, gy, gw, gh],
                    "alternatives": preds[1:3]
                })

                # Dibujar caja en capa de diagnóstico (Verde si >0.70, Amarillo si <0.70)
                box_color = (0, 210, 80) if conf >= 0.70 else (0, 180, 255)
                cv2.rectangle(diag_bboxes, (gx, gy), (gx + gw, gy + gh), box_color, 1)
                cv2.putText(diag_bboxes, top_char, (gx, max(12, gy - 3)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_color, 1, cv2.LINE_AA)

            # Decodificar palabra con contexto literario
            if char_preds_list:
                final_word, word_conf, alt_words = self.decode_word_with_coloane_context(char_preds_list)
                transcription_words.append({
                    "text": final_word,
                    "confidence": word_conf,
                    "bbox": s_word['word_bbox'],
                    "alternatives": alt_words
                })

        full_transcription = " ".join([w['text'] for w in transcription_words])
        avg_confidence = float(np.mean([w['confidence'] for w in transcription_words])) if transcription_words else 0.0

        # Guardar Capas de Diagnóstico
        base_name = f"diag_{session_id}"
        path_orig = os.path.join(OUT_DIR, f"{base_name}_orig.png")
        path_ink = os.path.join(OUT_DIR, f"{base_name}_ink.png")
        path_bbox = os.path.join(OUT_DIR, f"{base_name}_bbox.png")

        cv2.imwrite(path_orig, bgr)
        # Tinta pura en RGBA
        ink_rgba = cv2.cvtColor(clean_ink, cv2.COLOR_GRAY2BGRA)
        ink_rgba[:, :, 3] = clean_ink
        cv2.imwrite(path_ink, ink_rgba)
        cv2.imwrite(path_bbox, diag_bboxes)

        result = {
            "transcription": full_transcription,
            "average_confidence": round(avg_confidence, 3),
            "words_count": len(transcription_words),
            "words": transcription_words,
            "characters": analyzed_chars,
            "diagnostic_layers": {
                "original": f"/output_analisis/{base_name}_orig.png",
                "ink_isolated": f"/output_analisis/{base_name}_ink.png",
                "detection_boxes": f"/output_analisis/{base_name}_bbox.png"
            }
        }

        return result

    # =========================================================================
    # ALMACENAMIENTO DE RETROALIMENTACIÓN (AISLADO EN EXP 08)
    # =========================================================================
    def save_approved_transcription(self, image_name, raw_prediction, approved_text, user_notes=""):
        """Guarda la transcripción humana corregida exclusivamente dentro del sandbox del Exp 08."""
        record = {
            "id": f"trans_{int(os.path.getmtime(DB_APROBADAS_JSON) if os.path.exists(DB_APROBADAS_JSON) else 1000)}_{len(self.load_approved_transcriptions()) + 1}",
            "image_name": image_name,
            "raw_prediction": raw_prediction,
            "approved_text": approved_text,
            "user_notes": user_notes,
            "timestamp": str(np.datetime64('now'))
        }

        current = self.load_approved_transcriptions()
        current.append(record)

        with open(DB_APROBADAS_JSON, 'w', encoding='utf-8') as f:
            json.dump({"approved_transcriptions": current}, f, indent=2, ensure_ascii=False)

        # Guardar en CSV
        file_exists = os.path.exists(DB_APROBADAS_CSV)
        with open(DB_APROBADAS_CSV, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["id", "image_name", "raw_prediction", "approved_text", "user_notes", "timestamp"])
            writer.writerow([record["id"], record["image_name"], record["raw_prediction"], record["approved_text"], record["user_notes"], record["timestamp"]])

        print(f"✓ Transcripción Aprobada guardada en Exp 08: «{approved_text}»")
        return record

    def load_approved_transcriptions(self):
        if not os.path.exists(DB_APROBADAS_JSON):
            return []
        try:
            with open(DB_APROBADAS_JSON, 'r', encoding='utf-8') as f:
                return json.load(f).get("approved_transcriptions", [])
        except Exception:
            return []

def main():
    analyzer = ColoaneManuscriptAnalyzer()
    # Prueba rápida con el recorte real de "reyes" del Exp 07
    test_img = os.path.join(EXP07_DIR, "crops_palabras", "w_cap_1787545532551_01_reyes.png")
    if os.path.exists(test_img):
        print(f"\nProbando analizador con imagen real: {test_img}")
        res = analyzer.analyze_manuscript_image(test_img, session_id="test_reyes")
        print("\n" + "="*50)
        print(f"🎯 Transcripción Generada: «{res['transcription']}»")
        print(f"📊 Confianza Promedio: {res['average_confidence'] * 100:.1f}%")
        print(f"🔬 Letras Detectadas: {[c['char'] for c in res['characters']]}")
        print("="*50)

if __name__ == '__main__':
    main()
