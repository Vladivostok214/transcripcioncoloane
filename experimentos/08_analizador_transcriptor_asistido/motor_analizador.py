"""
Motor de Análisis y Transcripción Caligráfica Asistida (Exp 08 - Francisco Coloane)
==================================================================================
Pipeline Avanzado:
1. Preprocesador colorimétrico adaptativo: elimina subrayados de lápiz rojo,
   líneas de pauta y ruidos de renglones adyacentes.
2. Segmentación de palabras por bandas de densidad morfológica y valles de ligadura.
3. Extractor de Huellas Zonales (Grid 8x8 = 64 celdas) + Momentos Hu + IoU.
4. Decodificador Contextual Beam Search con el Léxico completo de Francisco Coloane (16,495 palabras).
5. Generación de capas de diagnóstico visual.
"""

import os
import sys
import json
import csv
import math
import cv2
import numpy as np

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

class ColoaneManuscriptAnalyzer:
    def __init__(self):
        self.glyphs_db = []
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

    def extract_features(self, binary_28x28):
        """Extrae vector de características: 64 densidades zonales (8x8) + 7 Momentos Hu."""
        # 1. Zoning 8x8 (64 celdas)
        grid_h, grid_w = 28 // 8, 28 // 8
        zoning = []
        for r in range(8):
            for c in range(8):
                cell = binary_28x28[r*grid_h:(r+1)*grid_h, c*grid_w:(c+1)*grid_w]
                zoning.append(np.mean(cell) / 255.0)

        # 2. Hu Moments
        moments = cv2.HuMoments(cv2.moments(binary_28x28)).flatten()
        log_hu = -np.sign(moments) * np.log10(np.abs(moments) + 1e-10)

        return np.array(zoning, dtype=np.float32), log_hu

    def prepare_glyph_templates(self):
        """Preprocesa cada glifo del catálogo para extracción de zonificación y momentos."""
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

            if img.shape[2] == 4:
                alpha = img[:, :, 3]
                mask = (alpha > 40).astype(np.uint8) * 255
            else:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

            pts = cv2.findNonZero(mask)
            if pts is None:
                continue
            x, y, w, h = cv2.boundingRect(pts)
            tight_mask = mask[y:y+h, x:x+w]

            resized = cv2.resize(tight_mask, (28, 28), interpolation=cv2.INTER_AREA)
            _, bin_norm = cv2.threshold(resized, 80, 255, cv2.THRESH_BINARY)

            zoning, log_hu = self.extract_features(bin_norm)

            self.glyph_templates[gid] = {
                "id": gid,
                "character": char,
                "position": g.get('position', 'media'),
                "binary": bin_norm,
                "zoning": zoning,
                "hu_moments": log_hu,
                "aspect_ratio": float(w) / max(1.0, float(h))
            }

    # =========================================================================
    # ETAPA 1: PREPROCESAMIENTO Y FILTRADO COLORIMÉTRICO ADAPTATIVO
    # =========================================================================
    def preprocess_image(self, bgr_img):
        """
        Elimina subrayados de lápiz rojo/color, sombras y ruidos de renglón adyacente.
        """
        h, w = bgr_img.shape[:2]
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

        # 1. CLAHE adaptativo para nivelar contraste
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        enh = clahe.apply(gray)
        den = cv2.bilateralFilter(enh, 5, 40, 40)

        # 2. Umbral adaptativo local
        bin_inv = cv2.adaptiveThreshold(den, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 6)

        # 3. Filtrado de lápiz rojo / trazos coloreados
        b, g, r = cv2.split(bgr_img)
        is_red = (r > 125) & (r > g.astype(int) + 15) & (r > b.astype(int) + 15)
        bin_inv[is_red] = 0

        # 4. Eliminación de líneas horizontales largas de pauta o subrayado
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (22, 1))
        h_lines = cv2.morphologyEx(bin_inv, cv2.MORPH_OPEN, h_kernel)
        clean_ink = cv2.subtract(bin_inv, h_lines)

        # 5. Filtrar intrusión inferior extrema si la imagen es alta
        if h > 35:
            clean_ink[int(h * 0.88):, :] = 0
            clean_ink[:int(h * 0.05), :] = 0

        # 6. Despeckle adaptativo
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(clean_ink, connectivity=8)
        clean_ink_final = np.zeros_like(clean_ink)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= 8:
                clean_ink_final[labels == i] = 255

        return clean_ink_final

    # =========================================================================
    # ETAPA 2: SEGMENTACIÓN DE PALABRAS Y LETRAS POR DENSIDAD Y LIGADURAS
    # =========================================================================
    def segment_words_and_characters(self, ink_mask):
        """Segmenta palabras respetando espacios y luego corta letras por valles de ligadura."""
        h, w = ink_mask.shape

        # Agrupar tinta en palabras mediante clausura horizontal suave
        kernel_w = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 1))
        word_bands = cv2.morphologyEx(ink_mask, cv2.MORPH_CLOSE, kernel_w)
        proj_x = np.sum(word_bands > 0, axis=0)

        # Detectar límites de palabras
        word_spans = []
        in_w = False
        start_x = 0
        gap = 0

        for x in range(w):
            val = proj_x[x]
            if val > 0:
                if not in_w:
                    in_w = True
                    start_x = x
                gap = 0
            else:
                if in_w:
                    gap += 1
                    if gap > 6 or x == w - 1:
                        end_x = x - gap
                        if end_x - start_x >= 10:
                            word_spans.append((start_x, end_x))
                        in_w = False
                        gap = 0

        if in_w and (w - start_x >= 10):
            word_spans.append((start_x, w - 1))

        if not word_spans:
            word_spans = [(0, w - 1)]

        # Fusionar palabras si la brecha es menor a 14px
        merged_words = []
        for span in word_spans:
            if not merged_words:
                merged_words.append(list(span))
            else:
                last = merged_words[-1]
                if span[0] - last[1] <= 10:
                    last[1] = span[1]
                else:
                    merged_words.append(list(span))

        # Para cada palabra, segmentar letras usando la métrica de 20.3px y valles
        segmented_words = []
        for (wx0, wx1) in merged_words:
            word_w = wx1 - wx0 + 1
            word_ink = ink_mask[:, wx0:wx1+1]

            pts = cv2.findNonZero(word_ink)
            if pts is None:
                continue
            bx, by, bw, bh = cv2.boundingRect(pts)
            tight_word_ink = word_ink[by:by+bh, bx:bx+bw]

            # Valles de densidad dentro de la palabra
            w_proj = np.sum(tight_word_ink > 0, axis=0)
            smoothed = np.convolve(w_proj, np.ones(5)/5, mode='same')

            valleys = []
            for x in range(5, bw - 5):
                if smoothed[x] <= smoothed[x-1] and smoothed[x] <= smoothed[x+1]:
                    valleys.append(x)

            # Cortes de letras con espaciado mínimo de 12px
            cuts = [0]
            for v in valleys:
                if v - cuts[-1] >= 12:
                    cuts.append(v)
            if bw - cuts[-1] < 10 and len(cuts) > 1:
                cuts.pop()
            cuts.append(bw)

            char_segments = []
            for i in range(len(cuts) - 1):
                cx0 = cuts[i]
                cx1 = cuts[i+1]
                sub_ink = tight_word_ink[:, cx0:cx1]
                
                c_pts = cv2.findNonZero(sub_ink)
                if c_pts is not None:
                    cbx, cby, cbw, cbh = cv2.boundingRect(c_pts)
                    char_segments.append({
                        "global_bbox": [wx0 + bx + cx0 + cbx, by + cby, cbw, cbh],
                        "sub_mask": sub_ink[cby:cby+cbh, cbx:cbx+cbw],
                        "is_initial": (i == 0),
                        "is_final": (i == len(cuts) - 2)
                    })

            segmented_words.append({
                "word_bbox": [wx0 + bx, by, bw, bh],
                "char_segments": char_segments
            })

        return segmented_words

    # =========================================================================
    # ETAPA 3: COTEJO MORFOLÓGICO AVANZADO (ZONING 8x8 + HU MOMENTS + IOU)
    # =========================================================================
    def match_character_segment(self, char_mask, is_initial=False, is_final=False):
        """Coteja el segmento contra las 114 plantillas usando zonificación 8x8."""
        if char_mask is None or char_mask.size == 0:
            return [("?", 0.0, "none")]

        h, w = char_mask.shape
        resized = cv2.resize(char_mask, (28, 28), interpolation=cv2.INTER_AREA)
        _, bin_norm = cv2.threshold(resized, 80, 255, cv2.THRESH_BINARY)

        zoning, log_hu = self.extract_features(bin_norm)
        aspect_ratio = float(w) / max(1.0, float(h))

        candidates_scores = {}

        for gid, tmpl in self.glyph_templates.items():
            char = tmpl['character']

            # 1. Similitud de Zonificación 8x8 (Coseno)
            norm_a = np.linalg.norm(zoning)
            norm_b = np.linalg.norm(tmpl['zoning'])
            zoning_sim = np.dot(zoning, tmpl['zoning']) / (norm_a * norm_b + 1e-6)
            zoning_sim = max(0.0, float(zoning_sim))

            # 2. Distancia Hu Moments
            hu_dist = np.linalg.norm(log_hu[:4] - tmpl['hu_moments'][:4])
            hu_score = np.exp(-hu_dist * 0.35)

            # 3. Solapamiento IoU
            intersection = np.logical_and(bin_norm > 0, tmpl['binary'] > 0).sum()
            union = np.logical_or(bin_norm > 0, tmpl['binary'] > 0).sum()
            iou_score = float(intersection) / max(1.0, float(union))

            # 4. Aspect Ratio
            ar_score = np.exp(-abs(aspect_ratio - tmpl['aspect_ratio']) * 1.0)

            # 5. Posición caligráfica
            pos_bonus = 1.0
            if is_initial and tmpl['position'] == 'inicial': pos_bonus = 1.15
            elif is_final and tmpl['position'] == 'final': pos_bonus = 1.15

            total_score = (zoning_sim * 0.45 + iou_score * 0.30 + hu_score * 0.15 + ar_score * 0.10) * pos_bonus

            if char not in candidates_scores or total_score > candidates_scores[char]['score']:
                candidates_scores[char] = {
                    "score": total_score,
                    "matched_id": gid,
                    "character": char
                }

        sorted_matches = sorted(candidates_scores.values(), key=lambda x: x['score'], reverse=True)
        top_matches = [(m['character'], round(float(m['score']), 3), m['matched_id']) for m in sorted_matches[:5]]
        return top_matches if top_matches else [("?", 0.0, "none")]

    # =========================================================================
    # ETAPA 4: DECODIFICADOR CONTEXTUAL CON LÉXICO COLOANE (BEAM SEARCH)
    # =========================================================================
    def decode_word_with_coloane_context(self, char_preds_list):
        """Busca en el vocabulario de 16,495 palabras de Coloane la mejor coincidencia."""
        raw_word = "".join([p[0][0] for p in char_preds_list])
        lower_raw = raw_word.lower()

        # Si coincide exactamente con una palabra del corpus
        if lower_raw in self.lexicon:
            return raw_word, 0.96, [raw_word]

        # Búsqueda difusa en el léxico
        candidates = []
        raw_len = len(raw_word)

        for vocab_word, freq in self.lexicon.items():
            v_len = len(vocab_word)
            if abs(v_len - raw_len) <= 2:
                # Similitud de caracteres compartidos
                matches = 0
                for i in range(min(raw_len, v_len)):
                    char_i = lower_raw[i]
                    if i < len(char_preds_list):
                        top_chars = [p[0].lower() for p in char_preds_list[i][:3]]
                        if vocab_word[i].lower() in top_chars:
                            matches += 1
                        elif char_i == vocab_word[i].lower():
                            matches += 1

                sim_ratio = matches / max(raw_len, v_len)
                if sim_ratio >= 0.50:
                    freq_bonus = min(1.0, math.log10(freq + 1) / 4.0)
                    score = sim_ratio * 0.70 + freq_bonus * 0.30
                    candidates.append((vocab_word, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        top_words = [c[0] for c in candidates[:3]]

        if top_words and candidates[0][1] >= 0.60:
            best_match = top_words[0]
            if raw_word and raw_word[0].isupper():
                best_match = best_match.capitalize()
            return best_match, round(candidates[0][1], 3), top_words

        return raw_word, round(np.mean([p[0][1] for p in char_preds_list]), 3), top_words

    # =========================================================================
    # PIPELINE COMPLETO Y GENERACIÓN DE CAPAS DE DIAGNÓSTICO
    # =========================================================================
    def analyze_manuscript_image(self, image_path, session_id=None):
        """Ejecuta el pipeline completo de análisis y diagnóstico."""
        session_id = session_id or str(int(os.path.getmtime(image_path) * 1000) if os.path.exists(image_path) else 1000)
        
        bgr = cv2.imread(image_path)
        if bgr is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen: {image_path}")

        h, w = bgr.shape[:2]

        # 1. Aislamiento de Tinta
        clean_ink = self.preprocess_image(bgr)

        # 2. Segmentación de Palabras y Letras
        segmented_words = self.segment_words_and_characters(clean_ink)

        transcription_words = []
        analyzed_chars = []
        diag_bboxes = bgr.copy()

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

                box_color = (0, 210, 80) if conf >= 0.70 else (0, 180, 255)
                cv2.rectangle(diag_bboxes, (gx, gy), (gx + gw, gy + gh), box_color, 1)
                cv2.putText(diag_bboxes, top_char, (gx, max(12, gy - 3)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_color, 1, cv2.LINE_AA)

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

    def save_approved_transcription(self, image_name, raw_prediction, approved_text, user_notes=""):
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
    test_img = os.path.join(UPLOADS_DIR, "upload_1787551810271.png")
    if os.path.exists(test_img):
        print(f"\nAnalizando imagen: {test_img}")
        res = analyzer.analyze_manuscript_image(test_img, session_id="test_upgrade")
        print("\n" + "="*55)
        print(f"🎯 Transcripción Generada: «{res['transcription']}»")
        print(f"📊 Confianza Promedio: {res['average_confidence'] * 100:.1f}%")
        print(f"📦 Palabras Reconocidas: {[w['text'] for w in res['words']]}")
        print("="*55)

if __name__ == '__main__':
    main()
