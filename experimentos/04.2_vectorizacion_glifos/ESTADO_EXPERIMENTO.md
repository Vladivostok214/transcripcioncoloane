# Estado del Experimento 04.2: Vectorización de Glifos Caligráficos
**Fecha de actualización:** 22 de Agosto de 2026  
**Estado general:** En pausa / Documentado y listo para reanudación  

---

## 1. Resumen Ejecutivo y Métricas

| Métrica | Cantidad | Porcentaje |
| :--- | :--- | :--- |
| **Total Glifos en el Dataset** | **103** | **100%** |
| **Aprobados (✓)** | **35** | **34.0%** |
| **Con Detalle / Ajuste Pendiente (⚡)** | **39** | **37.9%** |
| **Rechazados / Requieren Nueva Extracción (✕)** | **29** | **28.2%** |

---

## 2. Glifos Aprobados (35)
Estos glifos cumplen con la fidelidad caligráfica, curvas Bézier continuas y normalización en caja 1000×1000 sin ruido:

| ID | Carácter | Categoría | Línea / Origen |
| :--- | :---: | :--- | :--- |
| `g_p03_l01_titulo_top_01_T` | **T** | mayuscula | `p03_l01_titulo_top (3)` |
| `g_p03_l02_verso1_04_o` | **o** | minuscula | `p03_l02_verso1 (3)` |
| `g_p03_l02_verso1_07_n` | **n** | minuscula | `p03_l02_verso1 (3)` |
| `g_p03_l03_verso2_01_i` | **i** | minuscula | `p03_l03_verso2 (3)` |
| `g_p03_l03_verso2_02_c` | **c** | minuscula | `p03_l03_verso2 (3)` |
| `g_p03_l03_verso2_03_V` | **V** | mayuscula | `p03_l03_verso2 (3)` |
| `g_p03_l03_verso2_06_s` | **s** | minuscula | `p03_l03_verso2 (3)` |
| `g_p03_l03_verso2_07_a` | **a** | minuscula | `p03_l03_verso2 (3)` |
| `g_p03_l03_verso2_10_n` | **n** | minuscula | `p03_l03_verso2 (3)` |
| `g_p03_l03_verso2_11_n` | **n** | minuscula | `p03_l03_verso2 (3)` |
| `g_p03_l04_verso3_01_a` | **a** | minuscula | `p03_l04_verso3 (3)` |
| `g_p03_l04_verso3_03_s` | **s** | minuscula | `p03_l04_verso3 (3)` |
| `g_p03_l04_verso3_04_s` | **s** | minuscula | `p03_l04_verso3 (3)` |
| `g_p03_l07_verso6_04_j` | **j** | minuscula | `p03_l07_verso6 (3)` |
| `g_p03_l07_verso6_44_u002c` | **,** | signo | `p03_l07_verso6 (3)` |
| `g_p03_l07_verso6_06_u` | **u** | minuscula | `p03_l07_verso6 (3)` |
| `g_p03_l07_verso6_08_s` | **s** | minuscula | `p03_l07_verso6 (3)` |
| `g_p03_l07_verso6_09_e` | **e** | minuscula | `p03_l07_verso6 (3)` |
| `g_p03_l08_verso7_05_s` | **s** | minuscula | `p03_l08_verso7 (3)` |
| `g_p03_l08_verso7_44_u002c` | **,** | signo | `p03_l08_verso7 (3)` |
| `g_p03_l09_verso8_02_q` | **q** | minuscula | `p03_l09_verso8 (3)` |
| `g_p03_l13_rojo1_01_m` | **m** | minuscula | `p03_l13_rojo1 (3)` |
| `g_p03_l13_rojo1_03_s` | **s** | minuscula | `p03_l13_rojo1 (3)` |
| `g_p03_l13_rojo1_46_u002e` | **.** | signo | `p03_l13_rojo1 (3)` |
| `g_p03_l14_rojo2_01_y` | **y** | minuscula | `p03_l14_rojo2 (3)` |
| `g_p03_l15_rojo3_01_p` | **p** | minuscula | `p03_l15_rojo3 (3)` |
| `g_p02_l01_encabezado_02_a` | **a** | minuscula | `p02_l01_encabezado (2)` |
| `g_p02_l01_encabezado_58_u003a` | **:** | signo | `p02_l01_encabezado (2)` |
| `g_p02_l03_ezra2_34_u0022` | **"** | signo | `p02_l03_ezra2 (2)` |
| `g_p02_l04_ezra3_02_u` | **u** | minuscula | `p02_l04_ezra3 (2)` |
| `g_p02_l04_ezra3_03_r` | **r** | minuscula | `p02_l04_ezra3 (2)` |
| `g_p02_l05_ezra4_01_z` | **z** | minuscula | `p02_l05_ezra4 (2)` |
| `g_p02_l06_babel_03_1` | **1** | numero | `p02_l06_babel (2)` |
| `g_p02_l07_todoel_01_m` | **m** | minuscula | `p02_l07_todoel (2)` |
| `g_p02_l07_todoel_02_m` | **m** | minuscula | `p02_l07_todoel (2)` |

---

## 3. Glifos Con Detalle Anotado (39)
Glifos que tienen una vectorización base rescatable pero requieren micro-ajustes específicos registrados por el evaluador:

| ID | Carácter | Categoría | Observaciones y Detalles Específicos |
| :--- | :---: | :--- | :--- |
| `g_p03_l01_titulo_top_02_r` | **r** | minuscula | le falta la linea que baja hasta la parte inferior izquierda, , Suavizar bordes |
| `g_p03_l01_titulo_top_03_a` | **a** | minuscula | Unir trazo superior cortado |
| `g_p03_l01_titulo_top_04_v` | **v** | minuscula | Unir trazos cortado |
| `g_p03_l01_titulo_top_05_e` | **e** | minuscula | Unir trazos cortados |
| `g_p03_l01_titulo_top_06_s` | **s** | minuscula | la punta de la izquierda no debe terminar cortada, y le falta la linea que va hacia la derecha |
| `g_p03_l02_verso1_01_d` | **d** | minuscula | Unir trazo cortado, Cerrar panza de la letra |
| `g_p03_l02_verso1_02_e` | **e** | minuscula | Suavizar bordes, Unir trazo cortado |
| `g_p03_l02_verso1_03_l` | **l** | minuscula | esta es una letra l, no es un 1 |
| `g_p03_l02_verso1_05_e` | **e** | minuscula | esta es una e minuscula ligada, debe tener un bucle como una e |
| `g_p03_l02_verso1_06_s` | **s** | minuscula | parece una a pero es una s, hay que unir la linea superior y hacer un corte en la curva inferior |
| `g_p03_l03_verso2_04_g` | **g** | minuscula | Unir trazos cortados |
| `g_p03_l03_verso2_08_o` | **o** | minuscula | Unir trazos cortados, Suavizar bordes |
| `g_p03_l03_verso2_09_n` | **n** | minuscula | Suavizar bordes |
| `g_p03_l04_verso3_02_s` | **s** | minuscula | Unir trazo cortado, Suavizar bordes |
| `g_p03_l04_verso3_05_o` | **o** | minuscula | Cerrar panza de la letra, |
| `g_p03_l07_verso6_01_y` | **y** | minuscula | Unir trazos cortados |
| `g_p03_l07_verso6_02_h` | **h** | minuscula | Unir trazos cortados |
| `g_p03_l07_verso6_03_i` | **i** | minuscula | Eliminar mota / residuo, la linea que se ve en la parte inferior derecha |
| `g_p03_l07_verso6_07_s` | **s** | minuscula | Unir trazo cortado |
| `g_p03_l08_verso7_01_p` | **p** | minuscula | Unir trazo cortado |
| `g_p03_l08_verso7_02_r` | **r** | minuscula | le falta el extremo de la pata izquierda |
| `g_p03_l08_verso7_03_e` | **e** | minuscula | Unir trazo cortado |
| `g_p03_l08_verso7_04_g` | **g** | minuscula | Unir trazos cortados |
| `g_p03_l09_verso8_01_v` | **v** | minuscula | Unir trazo cortado |
| `g_p03_l09_verso8_03_r` | **r** | minuscula | Unir trazo cortado, y dibujar pata izquierda |
| `g_p03_l13_rojo1_02_e` | **e** | minuscula | Unir trazo cortado |
| `g_p03_l14_rojo2_02_U` | **U** | mayuscula | Unir trazos cortados |
| `g_p03_l15_rojo3_02_u` | **u** | minuscula | agregar pata izquierda |
| `g_p03_l16_bloque_01_P` | **P** | mayuscula | unir trazos cortados |
| `g_p02_l01_encabezado_01_c` | **c** | minuscula | unir trazos cortados |
| `g_p02_l01_encabezado_03_o` | **o** | minuscula | unir trazos cortados |
| `g_p02_l01_encabezado_04_n` | **n** | minuscula | el extremo inferior se ve cortado |
| `g_p02_l03_ezra2_01_x` | **x** | minuscula | Suavizar bordes |
| `g_p02_l04_ezra3_01_t` | **t** | minuscula | agregar extremos de la parte superior de la t |
| `g_p02_l05_ezra4_02_d` | **d** | minuscula | Suavizar bordes, Suavizar bordes |
| `g_p02_l06_babel_01_B` | **B** | mayuscula | reconstruis bucle del centro |
| `g_p02_l06_babel_02_b` | **b** | minuscula | Suavizar bordes |
| `g_p02_l06_babel_04_1` | **1** | numero | Unir trazo cortado |
| `g_cap_1787379184669_01_l` | **l** | minuscula | Suavizar bordes |

---

## 4. Glifos Rechazados (29)
Glifos que requieren una estrategia de binarización diferente (ej. lápiz verde, segmentación manual más limpia en Exp 04.1):

| ID | Carácter | Categoría | Motivo / Notas |
| :--- | :---: | :--- | :--- |
| `g_p03_l03_verso2_05_o` | **o** | minuscula | Requiere re-extracción o umbralización multi-escala |
| `g_p03_l10_verso9_01_L` | **L** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_p03_l10_verso9_02_A` | **A** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_p03_l10_verso9_03_S` | **S** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_p03_l10_verso9_04_I` | **I** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_p03_l10_verso9_05_S` | **S** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_p03_l10_verso9_06_D` | **D** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_p03_l10_verso9_07_E` | **E** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_p03_l10_verso9_08_T` | **T** | mayuscula | Unir trazo cortado |
| `g_p03_l10_verso9_09_R` | **R** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_p03_l10_verso9_10_A` | **A** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_custom_1787375326385_01_E` | **E** | mayuscula | Suavizar bordes |
| `g_custom_1787375326385_03_p` | **p** | minuscula | Suavizar bordes |
| `g_custom_1787375326385_04_u00e9` | **é** | minuscula | Suavizar bordes, le falta el acento |
| `g_custom_1787375326385_05_t` | **t** | minuscula | Suavizar bordes |
| `g_custom_1787375326385_06_t` | **t** | minuscula | Suavizar bordes |
| `g_custom_1787375326385_07_v` | **v** | minuscula | Requiere re-extracción o umbralización multi-escala |
| `g_custom_1787375657342_01_u00f1` | **ñ** | minuscula | Suavizar bordes |
| `g_cap_1787377048367_01_F` | **F** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_cap_1787377048367_02_C` | **C** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_cap_1787377048367_03_H` | **H** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_cap_1787377048367_04_R` | **R** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_cap_1787377161791_01_M` | **M** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_cap_1787377161791_02_N` | **N** | mayuscula | Requiere re-extracción o umbralización multi-escala |
| `g_cap_1787377598994_01_u00e1` | **á** | minuscula | Requiere re-extracción o umbralización multi-escala |
| `g_cap_1787377648006_01_n` | **n** | minuscula | Requiere re-extracción o umbralización multi-escala |
| `g_cap_1787377683634_01_u00e1` | **á** | minuscula | Requiere re-extracción o umbralización multi-escala |
| `g_cap_1787379122998_01_f` | **f** | minuscula | Requiere re-extracción o umbralización multi-escala |
| `g_cap_1787379291083_01_h` | **h** | minuscula | Suavizar bordes |

---

## 5. Arquitectura del Sistema y Herramientas Creadas

1. **`server_evaluador.py`**: Servidor local ligero (puerto 8002) basado en `ThreadingHTTPServer` que expone endpoints REST (`/api/dataset`, `/api/save_evaluation`) y sirve estáticos de forma instantánea.
2. **`evaluador_interactivo.html`**: SPA interactiva con visualización dividida 50/50 (Pluma Original vs SVG Renderizado en caja blanca), HUD flotante con botones directos (`✓ 1`, `⚡ 2`, `✕ 3`), atajos de teclado y guardado asíncrono persistente.
3. **`evaluacion_glifos.json`**: Base de datos JSON donde quedan registradas todas las calificaciones, timestamps y notas humanas.
4. **`svg/`**: Directorio con los 103 archivos `.svg` vectorizados en viewBox `0 0 1000 1000`.
5. **`dataset_glifos_vectoriales.json` y `.csv`**: Registros tabulares sincronizados con conteo de nodos Bézier y métricas tipográficas.

---

## 6. Hoja de Ruta para Reanudar el Experimento (Pipeline v3)

Cuando se retome este experimento, las siguientes tareas están listas para ser ejecutadas:

1. **Motor v3 - Binarización por Histéresis (Dual Thresholding):**
   - Utilizar un umbral alto para el núcleo del trazo y un umbral suave conectado para no perder los enlaces delgados ni las patas izquierdas de las letras.
2. **Cierre Morfológico Direccional:**
   - En lugar de un kernel elíptico estándar, aplicar kernels lineales orientados según el ángulo caligráfico (~45° o vertical) para cerrar bucles sin engrosar la anatomía.
3. **Ajuste y Reclasificación de los 39 Glifos con Detalle:**
   - Correr el script v3 sobre los 39 glifos anotados y verificar si pasan al estado de Aprobados.
4. **Tratamiento Especial para el Título en Lápiz Verde (`g_p03_l10_verso9_*`):**
   - Utilizar extracción por canal verde/inverso para separar el lápiz verde del fondo con alto contraste.
5. **Compilación de Fuente OpenType / TTF (Experimento 04.3):**
   - Convertir los SVG aprobados a curvas TrueType/CFF usando herramientas tipográficas para generar la fuente tipográfica instalable.