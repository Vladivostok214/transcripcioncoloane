# Atlas Caligráfico & Vectorial: Francisco Coloane (1977)
**Fase 2: Calibración Píxel a Píxel, Aislamiento de Trazo y Vectorización SVG**

---

## 1. Resumen de la Intervención

A partir de la retroalimentación sobre los recortes iniciales (donde algunos glifos captaban fragmentos de letras vecinas o desfasadas), se implementó un proceso de **re-calibración fina y vectorización algorítmica** estructurado en cuatro etapas:

1. **Re-extracción de Líneas Base con Calibración Geométrica:**
   - Se analizaron y fijaron los límites verticales y horizontales exactos de las líneas de texto en la **Página 2** (*Significaciones, Citas de Ezra Pound, Babel, Dalí*) y **Página 3** (*Travesías y Temporales, Estrofas en azul, Versos en rojo, Título en imprenta y Firma*).
   - Se generó una cuadrícula de coordenadas superpuestas píxel a píxel para asegurar que ningún glifo sufra solapamiento con letras adyacentes.

2. **Aislamiento de Trazo (Ink Separation Engine):**
   - **Tinta Azul/Negra:** Procesamiento en escala de grises con umbralización adaptativa/Otsu, eliminación de guías de renglón del cuaderno mediante apertura morfológica horizontal y filtrado de ruido.
   - **Tinta Roja Caligráfica:** Extracción en el espacio de color CIELAB a través del canal cromático $a^*$, permitiendo aislar la caligrafía roja (ej. *"Isla madre, sagrada..."*) sin interferencia de las manchas de papel o marcas subyacentes.

3. **Vectorización SVG Directa (`.svg`):**
   - Extracción de contornos jerárquicos (`cv2.RETR_CCOMP`) para preservar tanto los trazos exteriores como los huecos interiores (bucles de *e, o, a, d, g, B, P*).
   - Suavizado y aproximación de curvas con el algoritmo Douglas-Peucker ($\epsilon = 0.5$), generando paths SVG limpios, ligeros y escalables infinitamente sin pérdida de resolución.

4. **Visor Web Interactivo Multimodal (`abecedario_visual.html`):**
   - Incorpora selector de modos en tiempo real:
     - 📷 **Original Calibrado:** Recorte exacto de alta resolución con textura de papel y tinta original.
     - 🪄 **Tinta Aislada:** Imagen PNG transparente (32-bit RGBA) con fondo oscuro de alto contraste.
     - ⚡ **Vector SVG:** Gráficos vectoriales nativos escalables, listos para diseño, animación o exportación tipográfica.

---

## 2. Inventario Calibrado del Dataset

El dataset consta de **61 glifos catalogados** con metadatos completos en formatos `JSON` y `CSV`:

| Categoría | Total Muestras | Ejemplos Clave Aisaldos |
| :--- | :---: | :--- |
| **Mayúsculas (Imprenta)** | 10 | `T`, `E`, `M`, `P`, `O`, `R`, `A`, `L`, `S`, `Y` (*TEMPORALES Y*) |
| **Mayúsculas (Cursiva)** | 13 | `B` (*Babel*), `C` (*Coloane*), `E` (*Ezra*), `G` (*Génesis*), `I` (*Isla roja*), `L` (*La*), `P` (*Pound*), `S` (*Significaciones* / *Sagrada roja*), `T` (*Travesías*), `U` (*Un*), `V` (*Vientos*) |
| **Minúsculas (Cursiva)** | 29 | `a`, `b`, `c`, `d`, `e`, `f`, `g`, `h`, `i`, `j`, `l`, `m` (roja), `n`, `ñ`, `o`, `p`, `q`, `r`, `s`, `t`, `u`, `v`, `x`, `y`, `z`, vocales con tilde (`á`, `é`, `í`, `ó`) |
| **Dígitos Numéricos** | 3 | `1`, `7`, `9` (*1977*) |
| **Signos & Puntuación** | 6 | `«`, `»`, `:`, `,`, `.`, `…` (puntos suspensivos en rojo) |

---

## 3. Estructura de Archivos en el Proyecto

Los recursos calibrados y listos para su uso se encuentran organizados en la siguiente ruta:

- **Visor HTML Interactivo:**
  - [`experimentos/04_abecedario_glifos/abecedario_visual.html`](file:///C:/Users/WLADI/Desktop/COLOANE/TRANSCRIPCIONES%20COLOANE/experimentos/04_abecedario_glifos/abecedario_visual.html)
- **Vectores SVG Nativos:**
  - `experimentos/04_abecedario_glifos/svg_vectors/*.svg`
- **Imágenes Recortadas (Original & Aislada):**
  - `experimentos/04_abecedario_glifos/crops_raw/*.png`
  - `experimentos/04_abecedario_glifos/crops_isolated/*.png`
- **Bases de Datos Estructuradas:**
  - [`abecedario_glifos_coloane.json`](file:///C:/Users/WLADI/Desktop/COLOANE/TRANSCRIPCIONES%20COLOANE/experimentos/04_abecedario_glifos/abecedario_glifos_coloane.json)
  - [`abecedario_glifos_coloane.csv`](file:///C:/Users/WLADI/Desktop/COLOANE/TRANSCRIPCIONES%20COLOANE/experimentos/04_abecedario_glifos/abecedario_glifos_coloane.csv)
