# Experimento 07: Anotador & Analizador de Palabras y Ligaduras Cursivas (Local)

**Propósito:** Herramienta interactiva local diseñada para catalogar **palabras manuscritas completas** en alta resolución (300 DPI), analizar los puentes de unión cursiva (*ligaduras y coarticulación*) y extraer los puntos de anclaje de entrada/salida (*Entry & Exit Anchors*) de la caligrafía de Francisco Coloane.

---

## 🎯 Objetivos del Experimento

1. **Ground Truth a Nivel de Palabra (*Word-Level Annotation*):**
   - Recortar palabras completas (ej. *«Quemchi»*, *«cúter»*, *«temporales»*) sin amputar trazos ascendentes ni descendentes.
   - Generar pares de datos `[Imagen Palabra 300 DPI] <-> [Texto Transcrito]` para el pre-entrenamiento directo de modelos HTR (TrOCR / CRNN-CTC).

2. **Estudio y Extracción de Ligaduras Cursivas:**
   - Analizar cómo se enlazan pares de alta frecuencia (`de`, `en`, `es`, `co`, `tr`, `ll`, `ch`) en la mano de Coloane.
   - Identificar los puntos $(x_{out}, y_{out}) \rightarrow (x_{in}, y_{in})$ y el ángulo de empalme tangencial ($C^1$) de los trazos conectores.

3. **Insumo para el Experimento 08 (Síntesis Caligráfica de Nuevas Frases):**
   - Proporcionar las reglas geométricas y los glifos contextuales para componer palabras y párrafos sintéticos fluidos en los experimentos posteriores.

---

## 📁 Estructura del Experimento

```
experimentos/07_anotador_palabras_ligaduras/
├── README.md                           # Especificación del experimento
├── dataset_palabras_manuales.json      # Base de datos de palabras catalogadas
├── dataset_palabras_manuales.csv       # Formato tabular de palabras y coordenadas
├── crops_palabras/                     # Recortes originales de palabras completas (RGB 300 DPI)
├── crops_palabras_isolated/            # Recortes de palabras con tinta pura aislada (RGBA)
├── index.html                          # Interfaz web local para anotación de palabras y ligaduras
└── server_anotador_palabras.py         # Servidor HTTP local en Python
```
