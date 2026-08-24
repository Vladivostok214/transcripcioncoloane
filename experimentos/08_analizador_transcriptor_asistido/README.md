# Experimento 08: Analizador y Transcriptor Asistido (Coloane HTR Workbench)

**Propósito:** Proporcionar una plataforma de análisis y transcripción caligráfica asistida (*Human-in-the-Loop*) que tome fragmentos de manuscritos, limpie la tinta, coteje los trazos contra el catálogo de glifos y ligaduras, decodifique el texto usando el léxico de Francisco Coloane, y permita corregir y aprobar transcripciones en un entorno aislado.

---

## 🧠 Cerebro del Analizador (Lectura Multifuente)
El analizador consulta en modo solo-lectura:
1. **Catálogo de 114 Glifos (Exp 06):** Muestras con posición anatómica.
2. **Vectores SVG (Exp 04.2):** Formas vectoriales continuas.
3. **Métricas de Ligadura (Exp 07):** Constante de avance ($\Delta x \approx 20.3$ px) y valles de densidad vertical.
4. **Léxico de Francisco Coloane (Obsidian):** 16,495 palabras únicas y sus frecuencias literarias.

---

## 🔒 Sandbox Aislado (Escritura Exclusiva en Exp 08)
Todas las transcripciones generadas, corregidas y aprobadas por el usuario se guardan **únicamente** dentro de este experimento:
* `dataset_transcripciones_aprobadas.json`
* `dataset_transcripciones_aprobadas.csv`
* `uploads/`
* `output_analisis/`

*Ninguna base de datos de otros experimentos es modificada.*
