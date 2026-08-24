# 📖 Documento de Contexto y Arquitectura: Transcripción de Manuscritos Francisco Coloane
**Proyecto:** Transcripción y Reconocimiento Caligráfico de Manuscritos de Francisco Coloane  
**Última Actualización:** 24 de Agosto de 2026 (Sesión de Ingeniería, Métricas y Síntesis/Análisis)  
**Estado:** Ecosistema Modular en 4 Experimentos Activos (Exp 06 en Producción, Exp 07, Exp 07.1 y Exp 08 en Sandbox Local)  
**URL de Producción (Exp 06):** **[https://coloaneweb.vercel.app/](https://coloaneweb.vercel.app/)**  

---

## 1. Resumen Ejecutivo del Proyecto

El objetivo del proyecto es lograr la **transcripción, síntesis y reconocimiento óptico fidedigno de los manuscritos caligráficos del escritor chileno Francisco Coloane**, a partir de los escaneos de alta resolución (300 DPI) del libro *"Escritos y relato desde Quemchi" (1977)* y sus cuadernos manuscritos.

El proyecto ha avanzado a través de una **estrategia Bottom-Up modular y aislada**:
1. **Catálogo de Glifos Puros (Exp 06 - Producción Web):** Anotación colaborativa con clasificación por posición anatómica (`inicial`, `media`, `final`, `aislada`) y sincronización Supabase $\rightarrow$ GitHub $\rightarrow$ Local.
2. **Anotador de Palabras y Morfología de Ligaduras (Exp 07):** Extracción de palabras completas con herramienta de polígono multinodo, esqueletizado Zhang-Suen 1D y cálculo de constantes métricas de la pluma de Coloane ($\Delta x \approx 20.3\text{ px/letra}$).
3. **Sintetizador Caligráfico Cursivo de Frases (Exp 07.1):** Motor de composición de texto inédito multilínea, escala anatómica $x$-height, puentes Bézier $C^1$ continuos y soporte dual SVG Vectorial / Raster PNG.
4. **Analizador y Transcriptor Asistido (Exp 08):** Plataforma *Human-in-the-Loop* con soporte <kbd>Ctrl</kbd> + <kbd>V</kbd>, filtrado colorimétrico de lápiz rojo, zonificación $8\times 8$, decodificador contextual con el léxico de 16,495 palabras de Coloane y sandbox de guardado aislado.

---

## 2. Mapa y Puertos del Ecosistema de Experimentos

```
TRANSCRIPCIONES COLOANE/
├── corpus_coloane_obsidian/           # Corpus digitalizado completo de Francisco Coloane
│   ├── 01_libros_completos/           # Novelas y textos íntegros
│   ├── 02_cuentos_y_capitulos/        # Cuentos individuales
│   └── 03_analisis_lexico/            # Frecuencias (16,495 palabras) y N-gramas
│
├── experimentos/
│   ├── 02_segmentacion_lineas/        # 27 renglones originales a 300 DPI
│   ├── 03_dataset_ground_truth/       # Transcripciones Ground Truth iniciales
│   ├── 04.2_vectorizacion_glifos/     # 114 glifos vectorizados a curvas SVG (vtracer)
│   │
│   ├── 06_web_coloane/                # ★ EXP 06 (Producción Web / Vercel + Supabase)
│   │   ├── dataset_glifos_manuales.json # 114 glifos aprobados
│   │   ├── crops/ y crops_isolated/   # PNGs RGB y RGBA
│   │   └── server_anotador.py         # Puerto 8080 (Local) / Vercel (Producción)
│   │
│   ├── 07_anotador_palabras_ligaduras/# ★ EXP 07 (Anotador Local de Palabras)
│   │   ├── dataset_palabras_manuales.json # Catálogo de 12 palabras completas
│   │   ├── analizar_ligaduras.py      # Esqueletos Zhang-Suen y métricas topológicas
│   │   ├── analisis_ligaduras/        # Diagnósticos visuales 4-en-1 y metricas_ligaduras.json
│   │   └── server_anotador_palabras.py# Puerto 8085
│   │
│   ├── 07_1_sintetizador_frases_cursivas/ # ★ EXP 07.1 (Sintetizador Caligráfico)
│   │   ├── sintetizador_frases.py     # Generador CLI estático
│   │   ├── index.html                 # UI interactiva multilínea con puentes Bézier C1
│   │   └── server_sintetizador.py     # Puerto 8086
│   │
│   └── 08_analizador_transcriptor_asistido/ # ★ EXP 08 (HTR Workbench Asistido)
│       ├── motor_analizador.py        # Pipeline de 4 etapas + decodificador léxico
│       ├── index.html                 # UI Dual-Panel editable con soporte Ctrl+V
│       ├── dataset_transcripciones_aprobadas.json # Sandbox aislado de aprobaciones
│       └── server_transcriptor.py     # Puerto 8087
```

---

## 3. Avances Detallados por Experimento (Sesión del 24 de Agosto de 2026)

### 3.1 Experimento 06: Producción Web y Sincronización
* **Avance:** Sincronización local tras aprobación colaborativa en producción: **114 glifos individuales catalogados** en 49 caracteres únicos.
* **Clasificación Posicional:** Integración de los 4 chips (`📍 Inicial`, `📍 Media`, `📍 Final`, `📍 Aislada`) en el popover contextual con selección automática.
* **Resiliencia de Schema:** Manejo defensivo en `saveGlyphsToDatabase` ante actualizaciones de esquema en Supabase sin interrumpir la experiencia de usuario.

### 3.2 Experimento 07: Anotador de Palabras y Morfología de Ligaduras
* **Herramienta de Selección Avanzada:** Creación del modo de polígono multinodo con atajos inteligentes (<kbd>Enter</kbd>, <kbd>Backspace</kbd>, <kbd>DblClick</kbd>, <kbd>Esc</kbd>).
* **Pipeline de Adelgazamiento Zhang-Suen 1D (`analizar_ligaduras.py`):**
  * Procesa recortes de palabras para extraer el esqueleto central de la pluma.
  * Localiza automáticamente puntos terminales (verdes), bifurcaciones/lazos (fucsias), anclas de entrada (azul) y salida (amarillo).
* **Descubrimientos Métricos Cuantitativos en la Mano de Coloane:**
  * **Constante de Avance Horizontal:** **$\Delta x = 20.3 \pm 1.8$ px/letra** a 300 DPI (*reyes*: 21.0, *Aristóteles*: 19.6, *Schakespeare*: 20.8, *problemas*: 20.2, *griega*: 19.7, *sociales*: 18.1).
  * **Familias de Salida:** Salida baja (`a, e, d, m, n, t`) vs Salida alta (`o, r, v, w`) vs Bucle inferior (`g, j, y`).

### 3.3 Experimento 07.1: Sintetizador Caligráfico Cursivo de Frases
* **Normalización Anatómica de Escala ($x$-Height Normalization):**
  * Minúsculas medias (`a, c, e, o, r, s...`) normalizadas a **28 px**.
  * Ascendentes y mayúsculas (`l, d, b, t...`) normalizadas a **56 px** descansando en la línea base.
  * Descendentes (`g, p, y...`) normalizadas a **48 px** con cuerpo en línea base y cola colgante.
* **Puentes de Ligadura Bézier $C^1$:** Traza tangentes continuas entre el punto de salida exacto $(x_{out}, y_{out})$ y el de entrada $(x_{in}, y_{in})$.
* **Lienzo Dinámico y Multilínea:**
  * Soporte de párrafos y saltos de renglón manuales (<kbd>Enter</kbd>) y automáticos (*auto-wrap* a 950px).
  * Lienzo auto-expansible sin cortes horizontales con navegación y scroll fluido.
* **Motor Dual SVG Vectorial / Raster PNG:**
  * Conmutador en tiempo real entre curvas vectoriales puras (`.svg` sin artefactos de recorte) y mapas de bits (`.png`).
  * Exportador en **PNG 300 DPI** y **SVG Vectorial**.

### 3.4 Experimento 08: Analizador y Transcriptor Asistido (HTR Workbench)
* **Filosofía Human-in-the-Loop:** Entorno de transcripción con vista dual (diagnóstico visual de IA a la izquierda, editor de texto corregible a la derecha).
* **Pegado Directo con Portapapeles (<kbd>Ctrl</kbd> + <kbd>V</kbd>):** Permite pegar capturas directas de recortes de pantalla en milisegundos.
* **Preprocesador Colorimétrico Adaptativo:**
  * Discrimina y elimina subrayados de lápiz rojo y pautas de cuaderno que unen artificialmente las palabras.
  * Filtra intrusiones de renglones adyacentes superiores e inferiores.
* **Extractor Zonal $8\times 8$ + Momentos Hu + IoU:**
  * Segmenta por valles de densidad vertical y coteja la distribución estructural del trazo contra las 114 plantillas del catálogo.
* **Decodificador Contextual con el Corpus de Coloane:**
  * Valida las hipótesis visuales contra el diccionario de 16,495 palabras de Francisco Coloane mediante búsqueda difusa y bonificación de frecuencias.
* **Sandbox Aislado:**
  * Todas las transcripciones aprobadas por el usuario se registran exclusivamente en `dataset_transcripciones_aprobadas.json` y `.csv` dentro de la carpeta del Experimento 08, garantizando total inocuidad hacia los otros experimentos.

---

## 4. Estado de los Datos y Métricas Globales

* **Glifos Individuales en Producción (Exp 06):** 114 glifos (68 media, 37 inicial, 7 final, 2 aislada).
* **Glifos Vectorizados SVG (Exp 04.2):** 114 archivos `.svg` limpios.
* **Palabras Completas Catalogadas (Exp 07):** 12 palabras (*reyes, los, de, Como, dice, Aristóteles, Schakespeare, y, la, problemas, griega, sociales*).
* **Léxico y Frecuencias Literarias (Obsidian):** 16,495 palabras únicas y tablas de bigramas/trigramas.
* **Repositorio GitHub:** 100% sincronizado en rama `main` (commits limpios sin conflictos).

---

## 5. Hoja de Ruta para Futuras Sesiones de Optimización

1. **Expansión del Catálogo de Glifos y Palabras (Exp 06 & Exp 07):**
   * Seguir nutriendo variantes de letras complejas (`h`, `k`, `w`, `z`, mayúsculas) y palabras con ligaduras altas (`or`, `ov`, `br`).
2. **Generación de Dataset Masivo Sintético (Exp 07.1):**
   * Utilizar el sintetizador caligráfico para generar 50,000+ renglones sintéticos etiquetados a partir de los cuentos de Coloane.
3. **Entrenamiento de Modelo Neuronal Profundo (Exp 09 - HTR Deep Learning):**
   * Entrenar una red **TrOCR (Vision Transformer + BERT)** o **CRNN-CTC** pre-entrenada con el dataset sintético y validada con el dataset de transcripciones aprobadas del Exp 08.
4. **Aplicación Integral de Transcripción de Páginas Completas:**
   * Unificar segmentación de página $\rightarrow$ extracción de renglones $\rightarrow$ transcripción neuronal $\rightarrow$ corrección asistida en una suite unificada.
