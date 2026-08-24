"""
Script de Análisis Morfológico y Extracción de Ligaduras Cursivas (Exp 07)
==========================================================================
Procesa los recortes de palabras catalogadas, extrae el esqueleto 1D del trazo,
identifica puntos de bifurcación (lazos), extremos de trazo y calcula la métrica
de transición entre letras para Francisco Coloane.
"""

import os
import json
import numpy as np
import cv2
import matplotlib.pyplot as plt
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CROPS_DIR = os.path.join(BASE_DIR, 'crops_palabras')
CROPS_ISO_DIR = os.path.join(BASE_DIR, 'crops_palabras_isolated')
JSON_PATH = os.path.join(BASE_DIR, 'dataset_palabras_manuales.json')
OUT_DIR = os.path.join(BASE_DIR, 'analisis_ligaduras')

os.makedirs(OUT_DIR, exist_ok=True)

def zhang_suen_thinning(binary_image):
    """
    Algoritmo clásico de adelgazamiento morfológico Zhang-Suen
    Reduce trazos continuos a un esqueleto topológico de 1px.
    """
    skeleton = binary_image.copy() // 255
    prev = np.zeros_like(skeleton)
    
    while not np.array_equal(skeleton, prev):
        prev = skeleton.copy()
        
        # Paso 1
        mask1 = np.zeros_like(skeleton, dtype=bool)
        pad = np.pad(skeleton, 1, mode='constant')
        
        for i in range(1, pad.shape[0] - 1):
            for j in range(1, pad.shape[1] - 1):
                if pad[i, j] == 1:
                    p2 = pad[i - 1, j]
                    p3 = pad[i - 1, j + 1]
                    p4 = pad[i, j + 1]
                    p5 = pad[i + 1, j + 1]
                    p6 = pad[i + 1, j]
                    p7 = pad[i + 1, j - 1]
                    p8 = pad[i, j - 1]
                    p9 = pad[i - 1, j - 1]
                    
                    neighbors = [p2, p3, p4, p5, p6, p7, p8, p9]
                    B = sum(neighbors)
                    
                    if 2 <= B <= 6:
                        # Contar transiciones 0 -> 1
                        A = sum(neighbors[k] == 0 and neighbors[(k + 1) % 8] == 1 for k in range(8))
                        if A == 1:
                            if p2 * p4 * p6 == 0 and p4 * p6 * p8 == 0:
                                mask1[i - 1, j - 1] = True
        skeleton[mask1] = 0
        
        # Paso 2
        mask2 = np.zeros_like(skeleton, dtype=bool)
        pad = np.pad(skeleton, 1, mode='constant')
        
        for i in range(1, pad.shape[0] - 1):
            for j in range(1, pad.shape[1] - 1):
                if pad[i, j] == 1:
                    p2 = pad[i - 1, j]
                    p3 = pad[i - 1, j + 1]
                    p4 = pad[i, j + 1]
                    p5 = pad[i + 1, j + 1]
                    p6 = pad[i + 1, j]
                    p7 = pad[i + 1, j - 1]
                    p8 = pad[i, j - 1]
                    p9 = pad[i - 1, j - 1]
                    
                    neighbors = [p2, p3, p4, p5, p6, p7, p8, p9]
                    B = sum(neighbors)
                    
                    if 2 <= B <= 6:
                        A = sum(neighbors[k] == 0 and neighbors[(k + 1) % 8] == 1 for k in range(8))
                        if A == 1:
                            if p2 * p4 * p8 == 0 and p2 * p6 * p8 == 0:
                                mask2[i - 1, j - 1] = True
        skeleton[mask2] = 0
        
    return skeleton * 255

def analyze_skeleton_topology(skeleton):
    """
    Encuentra puntos finales (endpoints) y puntos de bifurcación (branch points).
    """
    skel = (skeleton > 0).astype(np.uint8)
    endpoints = []
    branchpoints = []
    
    h, w = skel.shape
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if skel[y, x] == 1:
                # 8-vecindario
                patch = skel[y - 1:y + 2, x - 1:x + 2]
                n_neighbors = np.sum(patch) - 1
                
                # Transiciones 0 -> 1
                p = [patch[0, 1], patch[0, 2], patch[1, 2], patch[2, 2],
                     patch[2, 1], patch[2, 0], patch[1, 0], patch[0, 0]]
                transitions = sum(p[k] == 0 and p[(k + 1) % 8] == 1 for k in range(8))
                
                if transitions == 1:
                    endpoints.append((x, y))
                elif transitions >= 3:
                    branchpoints.append((x, y))
                    
    return endpoints, branchpoints

def process_all_words():
    if not os.path.exists(JSON_PATH):
        print("No se encontró dataset_palabras_manuales.json")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    words = data.get('words', [])
    print(f"Iniciando análisis morfológico de {len(words)} palabras...")

    summary_metrics = []

    for idx, w in enumerate(words):
        word_text = w.get('word_text', 'unknown')
        word_id = w.get('id', f'w_{idx}')
        iso_file = os.path.join(CROPS_ISO_DIR, w.get('crop_isolated_file', ''))
        rgb_file = os.path.join(CROPS_DIR, w.get('crop_file', ''))

        if not os.path.exists(iso_file) or not os.path.exists(rgb_file):
            continue

        # Cargar imágenes
        img_rgb = Image.open(rgb_file).convert('RGB')
        img_iso = Image.open(iso_file).convert('RGBA')

        # Extraer canal alfa (máscara de tinta pura)
        alpha = np.array(img_iso)[:, :, 3]
        binary = (alpha > 50).astype(np.uint8) * 255

        # Esqueletización
        skeleton = zhang_suen_thinning(binary)

        # Topología del grafo
        endpoints, branchpoints = analyze_skeleton_topology(skeleton)

        # Perfil de proyección vertical (densidad por columna x)
        v_proj = np.sum(binary > 0, axis=0)
        h_proj = np.sum(binary > 0, axis=1)

        # Ancho por carácter promedio
        char_count = len(word_text)
        width_px = binary.shape[1]
        height_px = binary.shape[0]
        avg_char_width = round(width_px / max(1, char_count), 1)

        # Determinar punto de inicio más a la izquierda y punto final más a la derecha
        skel_points = np.argwhere(skeleton > 0)
        if len(skel_points) > 0:
            leftmost = tuple(skel_points[np.argmin(skel_points[:, 1])][::-1]) # (x, y)
            rightmost = tuple(skel_points[np.argmax(skel_points[:, 1])][::-1]) # (x, y)
        else:
            leftmost = (0, 0)
            rightmost = (width_px, height_px)

        word_metric = {
            "id": word_id,
            "word": word_text,
            "character_count": char_count,
            "category": w.get('category', ''),
            "width_px": width_px,
            "height_px": height_px,
            "avg_char_width_px": avg_char_width,
            "stroke_pixels": int(np.sum(skeleton > 0)),
            "endpoints_count": len(endpoints),
            "branchpoints_count": len(branchpoints),
            "entry_anchor": [int(leftmost[0]), int(leftmost[1])],
            "exit_anchor": [int(rightmost[0]), int(rightmost[1])]
        }
        summary_metrics.append(word_metric)

        # =========================================================================
        # GENERAR PANEL DE DIAGNÓSTICO VISUAL 4-EN-1
        # =========================================================================
        fig, axes = plt.subplots(2, 2, figsize=(10, 6), facecolor='#0b0f19')

        # 1. RGB Original
        axes[0, 0].imshow(img_rgb)
        axes[0, 0].set_title(f"1. Manuscrito RGB: «{word_text}»", color='#38bdf8', fontsize=11, fontweight='bold')
        axes[0, 0].axis('off')

        # 2. Tinta Pura Aislada
        axes[0, 1].imshow(alpha, cmap='gray')
        axes[0, 1].set_title("2. Máscara de Tinta Pura (RGBA)", color='#a855f7', fontsize=11, fontweight='bold')
        axes[0, 1].axis('off')

        # 3. Esqueleto 1px y Nodos
        axes[1, 0].imshow(np.zeros((height_px, width_px, 3), dtype=np.uint8))
        axes[1, 0].imshow(skeleton, cmap='Blues', alpha=0.9)
        # Dibujar endpoints en verde
        for ep in endpoints:
            axes[1, 0].plot(ep[0], ep[1], 'o', color='#34d399', markersize=5, label='Endpoint' if ep == endpoints[0] else "")
        # Dibujar branchpoints en rojo/fucsia
        for bp in branchpoints:
            axes[1, 0].plot(bp[0], bp[1], 'x', color='#f43f5e', markersize=6, label='Bifurcación' if bp == branchpoints[0] else "")
        # Dibujar anclas
        axes[1, 0].plot(leftmost[0], leftmost[1], 's', color='#38bdf8', markersize=7, label='Entrada')
        axes[1, 0].plot(rightmost[0], rightmost[1], '^', color='#fbbf24', markersize=7, label='Salida')

        axes[1, 0].set_title(f"3. Esqueleto 1D ({len(endpoints)} extremos, {len(branchpoints)} lazos)", color='#34d399', fontsize=11, fontweight='bold')
        axes[1, 0].axis('off')

        # 4. Perfil de Densidad y Ligaduras (Valles entre letras)
        axes[1, 1].set_facecolor('#070a10')
        x_axis = np.arange(len(v_proj))
        axes[1, 1].plot(x_axis, v_proj, color='#38bdf8', lw=1.5, label='Densidad vertical')
        axes[1, 1].axhline(np.mean(v_proj), color='#94a3b8', linestyle='--', alpha=0.5, label='Media')
        axes[1, 1].set_title("4. Perfil de Transición & Valles de Ligadura", color='#fbbf24', fontsize=11, fontweight='bold')
        axes[1, 1].tick_params(colors='#94a3b8', labelsize=8)
        axes[1, 1].grid(True, color='#1e293b', linestyle=':')

        plt.tight_layout()
        out_plot = os.path.join(OUT_DIR, f"analisis_{word_id}.png")
        plt.savefig(out_plot, dpi=180, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close()

        print(f"  [{idx+1}/{len(words)}] «{word_text}» analizado -> {os.path.basename(out_plot)}")

    # Guardar reporte JSON
    metrics_path = os.path.join(OUT_DIR, 'metricas_ligaduras.json')
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(summary_metrics, f, ensure_ascii=False, indent=2)

    print("="*60)
    print(f"Análisis completo guardado en: {OUT_DIR}")
    print(f"Métricas estructuradas en: {metrics_path}")

if __name__ == '__main__':
    process_all_words()
