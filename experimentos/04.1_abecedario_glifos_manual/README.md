# Experimento 04.1: Anotador Manual de Glifos (Francisco Coloane)

Esta herramienta interactiva permite recortar, clasificar y catalogar con precisión milimétrica cada letra y carácter manuscrito presente en los renglones a 300 DPI de los cuadernos de Francisco Coloane.

---

## 🚀 Acceso Rápido a la Interfaz

La aplicación web local se encuentra activa en tu navegador en la siguiente dirección:

👉 **http://127.0.0.1:8080**

*(Para iniciar o reiniciar el servidor en cualquier momento, ejecuta: python server_anotador.py dentro de esta carpeta).*

---

## 🛠️ Flujo de Trabajo y Modo de Uso

1. **Selección de Renglón:**
   - Usa los botones [◀ Anterior] y [Siguiente ▶] o el desplegable superior para cambiar entre los 27 renglones disponibles.
   - En la barra superior verás el **Texto de Referencia (*Ground Truth*)** para saber exactamente qué frase o verso estás anotando.

2. **Navegación y Zoom en el Renglón:**
   - **Zoom:** Rueda del mouse hacia arriba/abajo (o botones + / -).
   - **Paneo / Desplazamiento:** Clic derecho o botón central del mouse y arrastra el lienzo.

3. **Selección y Asignación de Glifos:**
   - Haz **clic izquierdo y arrastra** sobre el lienzo para dibujar un rectángulo alrededor de la letra.
   - Al soltar el mouse, se abrirá el panel flotante de asignación:
     - **Letra / Carácter:** Escribe el carácter (ej. T, , 7, «).
     - **Categoría Caligráfica (Desplegable):**
       - 🔠 Mayúscula
       - 🔡 Minúscula
       - 🔢 Número
       - ✒️ Signo de Puntuación
       - 🔗 Ligadura / Par de letras
       - 🎨 Símbolo / Trazo Especial
     - **Nota / Contexto (Opcional):** ej. *T inicial cursiva*, *tinta roja*, *s final*.
     - Presiona **Enter** o el botón *Asignar*.

4. **Guardar en la Base de Datos:**
   - Al terminar de etiquetar las letras de un renglón, presiona el botón verde **💾 Guardar Renglón en Base de Datos**.
   - Esto generará automáticamente:
     - Recortes originales en alta resolución en crops/.
     - Recortes con tinta aislada y fondo transparente en crops_isolated/.
     - Actualización instantánea en dataset_glifos_manuales.json y dataset_glifos_manuales.csv.

---

## ⌨️ Atajos de Teclado

* **Enter**: Confirmar y asignar el glifo seleccionado en el formulario.
* **Escape**: Cancelar la selección activa.
* **Ctrl + S**: Guardar el renglón actual en la base de datos.
* **D o Flecha Derecha**: Ir al siguiente renglón.
* **A o Flecha Izquierda**: Ir al renglón anterior.
* **R**: Resetear el zoom y centrar el renglón.
