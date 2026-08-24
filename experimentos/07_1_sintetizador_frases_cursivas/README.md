# Experimento 07.1: Sintetizador de Frases & Enlaces Cursivos (Coloane Handwriting Synthesizer)

**Propósito:** Componer frases y textos nuevos e inéditos ensamblando los **glifos individuales del Experimento 06** guiados por las **métricas de ligadura y separación horizontal ($\Delta x \approx 20$ px) del Experimento 07**.

---

## 🎯 Capacidades del Experimento 07.1

1. **Selección Contextual de Glifos (*Context-Aware Glyphs*):**
   - Elige automáticamente glifos `inicial`, `media` y `final` según la posición de la letra en la palabra.
   - Alterna entre múltiples muestras del catálogo para simular la variación orgánica de la mano humana (*anti-rigidez tipográfica*).

2. **Puentes de Ligadura Bézier $C^1$:**
   - Calcula empalmes tangenciales continuos entre el punto de salida $(x_{out}, y_{out})$ y el punto de entrada $(x_{in}, y_{in})$.

3. **Cotejo con el Ground Truth del Exp 07:**
   - Compara directamente la frase sintética (ej. *«los reyes y aristóteles»*) contra los recortes reales del manuscrito.

4. **Exportación Dual:**
   - Exporta imágenes compuestas en PNG 300 DPI y vectores SVG escalables.
