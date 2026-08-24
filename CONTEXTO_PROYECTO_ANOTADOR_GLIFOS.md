# 📖 Documento de Contexto y Arquitectura: Anotador Manual y Catálogo de Glifos
**Proyecto:** Transcripción y Reconocimiento de Manuscritos de Francisco Coloane  
**Experimento Activo (Producción):** `06_web_coloane` (Fuente Única de Verdad)  
**URL de Producción:** **[https://coloaneweb.vercel.app/](https://coloaneweb.vercel.app/)**  
**Fecha de Checkpoint:** 23 de Agosto de 2026  
**Estado:** 100% Operativo y Desplegado en Vercel con buffer Supabase y sync a GitHub

> [!TIP]
> **🚀 Acceso Web Directo:**
> Navegar a **[https://coloaneweb.vercel.app/](https://coloaneweb.vercel.app/)** desde cualquier navegador o dispositivo.
> Para levantar servidor de desarrollo local:
> ```powershell
> python experimentos/06_web_coloane/server_anotador.py
> ```

---

## 1. Resumen Ejecutivo y Estado del Proyecto

El objetivo central del proyecto es lograr la **transcripción y el reconocimiento óptico fidedigno de los manuscritos caligráficos del escritor chileno Francisco Coloane**, a partir de los escaneos de alta resolución (300 DPI) del libro *"Escritos y relato desde Quemchi" (1977)*.

Tras evaluar y descartar los modelos genéricos de Visión-Lenguaje (VLM / HTR del Experimento 05) debido a que la caligrafía cursiva e inclinada de Coloane provocaba tasas de error inaceptables (94% – 112% CER), el proyecto adoptó una **metodología Bottom-Up** colaborativa fundamentada en:
1. Construir un **Catálogo Arquetípico de Glifos Puros** mediante una herramienta interactiva web de alta precisión desplegada en la nube.
2. Extraer de forma aislada la tinta (máscaras RGBA sin fondo de papel) en el cliente mediante JS nativo (0.2 ms por glifo).
3. Acopio y curaduría continua: los colaboradores anotan en la web $\rightarrow$ almacenamiento en buffer temporal (Supabase) $\rightarrow$ revisión por el administrador (`Wladimir`) $\rightarrow$ consolidación automática en GitHub en 1 commit $\rightarrow$ sincronización local (`git pull`).
4. Establecer una base de datos estructurada en JSON y CSV que sirve como diccionario maestro para los experimentos de vectorización SVG (`04.2_vectorizacion_glifos`) y búsqueda interactiva (`05_spotting_glifos_interactivo`).

Al momento de este checkpoint, se han clasificado y verificado **105 glifos individuales** correspondientes a **49 caracteres únicos**.

---

## 2. Historial de Decisiones y Archivo Histórico

Los documentos de informes iniciales y especificaciones preliminares desactualizadas han sido archivados en el directorio `_archivo_historico/` para mantener la raíz limpia y enfocada:
* `_archivo_historico/INFORME_EXPERIMENTACION_01.md`: Pruebas iniciales de binarización y preprocesamiento de color.
* `_archivo_historico/INFORME_TECNICO_ATLAS_CALIGRAFICO.md`: Hipótesis conceptual sobre segmentación basada en proyección de perfiles.
* `_archivo_historico/Spec Driven Development.txt`: Especificación técnica preliminar anterior al pivote interactivo.

---

## 3. Arquitectura del Experimento 06 (`experimentos/06_web_coloane`)

```
TRANSCRIPCIONES COLOANE/
├── experimentos/
│   ├── 02_segmentacion_lineas/
│   │   └── crops/                     # 27 renglones recortados a 300 DPI (p02 y p03)
│   ├── 03_dataset_ground_truth/
│   │   └── dataset_muestras_p02_p03.json  # Transcripciones Ground Truth
│   ├── 04.2_vectorizacion_glifos/     # Pipeline SVG -> Consume 06_web_coloane
│   ├── 05_spotting_glifos_interactivo/# Motor de Spotting -> Consume 06_web_coloane
│   └── 06_web_coloane/                # ★ FUENTE ÚNICA OFICIAL DEL CATÁLOGO (Vercel)
│       ├── index.html                 # UI Frontend SPA interactiva (Noir-Tech, JS Ink Isolation)
│       ├── dataset_glifos_manuales.json # Base de datos JSON maestra de glifos
│       ├── dataset_glifos_manuales.csv  # Base de datos tabular CSV maestra
│       ├── crops/                     # Recortes originales de cada glifo (RGB)
│       ├── crops_isolated/            # Recortes de tinta aislada con canal alfa (RGBA)
│       ├── api/
│       │   └── sync_github.js         # Función Serverless Vercel (Sync Supabase -> GitHub)
│       ├── sync_from_supabase.py      # Herramienta CLI de sincronización local
│       ├── setup_supabase.sql         # Script DDL/Storage para Supabase
│       ├── vercel.json                # Configuración de despliegue en Vercel
│       └── server_anotador.py         # Backend HTTP Python para desarrollo local
```

---

## 4. Funcionamiento del Backend (`server_anotador.py`)

El servidor es una aplicación ligera en Python basada en `http.server.HTTPServer` configurada en el puerto **`8000`** para máxima compatibilidad con Windows y navegadores modernos.

### 4.1 Endpoints de la API REST:
* `GET /` o `GET /index.html`: Sirve la aplicación frontend interactiva.
* `GET /api/init_data`: Retorna los 27 renglones del Ground Truth junto con la base de datos completa de glifos guardados.
* `GET /api/image?line_id=<id>`: Entrega la imagen PNG del renglón original desde el directorio de segmentación.
* `GET /crops/<filename>`: Sirve el archivo PNG del recorte original del glifo.
* `GET /crops_isolated/<filename>`: Sirve el archivo PNG de tinta pura aislada.
* `GET /api/glyphs`: Retorna el estado actual de la base de datos de glifos en formato JSON.
* `POST /api/save_line`:
  1. Recibe el listado de cajas delimitadoras (*Bounding Boxes*) asignadas a un renglón.
  2. Utiliza **Pillow** para recortar físicamente el área seleccionada y guardarla en `crops/`.
  3. Procesa el recorte mediante el **algoritmo de aislamiento de tinta** y guarda el resultado en `crops_isolated/`.
  4. Actualiza atómicamente `dataset_glifos_manuales.json` y `dataset_glifos_manuales.csv`.
* `POST /api/delete_glyph`: Permite eliminar un glifo individual específico de la base de datos en tiempo real.

### 4.2 Algoritmo de Aislamiento de Tinta:
Para cada recorte de glifo:
1. Se convierte la imagen a escala de grises.
2. Se aplica una umbralización adaptativa Gaussiana invertida (`cv2.adaptiveThreshold` con bloque de 21 y constante 10), separando la tinta de las imperfecciones y variaciones de tono del papel.
3. Se aplica una apertura morfológica (`cv2.morphologyEx` con kernel $2\times 2$) para suprimir el ruido de grano fino.
4. Se construye una imagen de 4 canales **RGBA**: color de tinta constante (`#F0F0F0`) con la máscara binarizada asignada directamente al canal **Alfa**, permitiendo una representación pura y sin fondo de los trazos de Coloane.

---

## 5. Funcionamiento del Frontend (`index.html`)

La interfaz está diseñada con una estética **Noir-Tech** optimizada para trabajo de anotación intensivo, con soporte completo de aceleración por hardware:

### 5.1 Motor Gráfico Canvas 2D
* **Cámara Virtual Nativa**: El lienzo `<canvas>` abarca el 100% del área de trabajo y renderiza mediante matrices afines (`ctx.translate`, `ctx.scale`), eliminando cualquier desfase de subpíxeles introducido por estilos CSS.
* **Mapeo Lineal Invertido**:
  $$\text{imgX} = \frac{\text{clientX} - \text{viewport.left} - \text{panX}}{\text{zoom}}$$
  $$\text{imgY} = \frac{\text{clientY} - \text{viewport.top} - \text{panY}}{\text{zoom}}$$
* **Zoom y Paneo Fluido**: Zoom dinámico centrado en el cursor mediante la rueda del ratón y paneo infinito con clic derecho o botón central.

### 5.2 Herramienta de Selección y Asignación
* **Bounding Box Elástico**: Al arrastrar con el botón izquierdo sobre el renglón se dibuja el marco de selección con visualización de línea discontinua de grosor constante (`lineWidth = 2.5 / zoom`).
* **Popover Contextual de Clasificación**:
  - Muestra una **previsualización 1:1** exacta del recorte seleccionado en `#previewCanvas`.
  - Campo de entrada para el **Carácter Exacto** (ej. `a`, `T`, `«`, `1`).
  - Menú desplegable con categorías: *Mayúscula, Minúscula, Número, Signo de Puntuación, Ligadura, Símbolo*.
  - Campo opcional para **Notas / Contexto** (ej. *T inicial, bucle cerrado*).
* **Atajos de Teclado**:
  - `Enter`: Asignar glifo y cerrar popover.
  - `Esc`: Cancelar selección o cerrar modales.
  - `Ctrl + S`: Guardar renglón en la base de datos.
  - `D` / `Flecha Derecha`: Avanzar al siguiente renglón.
  - `A` / `Flecha Izquierda`: Retroceder al renglón anterior.
  - `R`: Ajustar zoom a pantalla.

---

## 6. Panel de Catálogo y Cobertura del Abecedario

Accesible a través del botón superior **"📊 Catálogo & Cobertura"**:

### 6.1 Cuadrícula del Abecedario y Semáforo de Cobertura
* Presenta el abecedario español completo subdividido en:
  - **🔡 Minúsculas** (`a` a `z` + vocales con tilde).
  - **🔠 Mayúsculas** (`A` a `Z` + vocales con tilde).
  - **🔢 Números y ✒️ Signos de puntuación**.
  - **🔗 Ligaduras y caracteres especiales**.
* **Código de Colores Dinámico**:
  - ⚪ **Gris con borde punteado (0)**: Letra pendiente por capturar.
  - 🟡 **Amarillo (1 muestra)**: Cobertura inicial básica.
  - 🟢 **Verde Esmeralda con brillo (2+ muestras)**: Cobertura sólida con variedad de muestras.

### 6.2 Inspector y Galería de Glifos
* Al hacer clic en cualquier letra de la cuadrícula:
  - Se visualizan todas las muestras capturadas para ese carácter.
  - **Vista Dual**: Cada tarjeta incluye el **Recorte Original** del manuscrito y el **Recorte de Tinta Pura Aislada**.
  - Metadatos: Renglón de origen, Página, Dimensiones en píxeles y Notas.
  - **🗑️ Botón de eliminación en caliente**: Permite remover una muestra específica si se detecta alguna imperfección o trazo vecino parásito, actualizando inmediatamente la base de datos.

---

## 7. Métricas y Estado de la Base de Datos al Checkpoint

### Resumen General:
* **Total de glifos guardados:** **105 muestras**
* **Caracteres únicos clasificados:** **49 caracteres**
* **Renglones / fuentes procesados:** 30 fuentes y renglones anotados con muestras puras (páginas 2, 3 y capturas externas).

### Desglose por Categoría:

| Categoría | Glifos Capturados | Caracteres Únicos | Cobertura del Abecedario Base |
| :--- | :---: | :---: | :--- |
| **🔡 Minúsculas** | **76** | **27** *(25 base + `á`, `é`)* | **92.6% (25 de 27 letras)** |
| **🔠 Mayúsculas** | **22** | **17** | **63.0% (17 de 27 letras)** |
| **✒️ Signos** | **5** | **4** | Comas (`,`), Comillas (`"`), Puntos (`.`), Dos puntos (`:`) |
| **🔢 Números** | **2** | **1** | Dígito `1` |

### Detalle de Caracteres Capturados:
* **Minúsculas capturadas (27):** `s` (11), `n` (7), `e` (6), `o` (5), `a` (4), `r` (4), `m` (3), `p` (3), `t` (3), `u` (3), `v` (3), `c` (2), `d` (2), `g` (2), `h` (2), `i` (2), `l` (2), `y` (2), `á` (2), `b` (1), `f` (1), `j` (1), `q` (1), `x` (1), `z` (1), `é` (1), `ñ` (1).
* **Minúsculas faltantes del abecedario base (2):** `k`, `w`. *(Se capturaron con éxito las prioritarias `f` y `ñ`, además de las vocales tildadas `á` y `é`)*.
* **Mayúsculas capturadas (17):** `A` (2), `E` (2), `R` (2), `S` (2), `T` (2), `B` (1), `C` (1), `D` (1), `F` (1), `H` (1), `I` (1), `L` (1), `M` (1), `N` (1), `P` (1), `U` (1), `V` (1).
* **Mayúsculas faltantes del abecedario base (10):** `G`, `J`, `K`, `Ñ`, `O`, `Q`, `W`, `X`, `Y`, `Z`.

---

## 8. Guía de Uso Rápido

1. Asegurarse de que el servidor esté activo:
   ```powershell
   python experimentos/04.1_abecedario_glifos_manual/server_anotador.py 8000
   ```
2. Abrir el navegador en **`http://localhost:8000`**.
3. Navegar entre los renglones usando las teclas `A` / `D` o el selector superior.
4. Seleccionar con el mouse los caracteres más limpios y presionar `Enter` tras escribir la letra correspondiente.
5. Presionar **"Guardar Renglón"** (`Ctrl + S`).
6. Consultar el botón **"📊 Catálogo & Cobertura"** para monitorear el progreso y verificar la calidad de las muestras aisladas.
