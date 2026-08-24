# 🖋️ Transcripciones Francisco Coloane: Reconocimiento y Síntesis Caligráfica de Manuscritos

> **Proyecto de Humanidades Digitales e Inteligencia Artificial:** Rescate, catalogación, síntesis y transcripción asistida de los manuscritos originales del célebre escritor chileno **Francisco Coloane** (1910–2002).

[![Vercel Deployment](https://img.shields.io/badge/Producci%C3%B3n%20Web-coloaneweb.vercel.app-blue?style=flat&logo=vercel)](https://coloaneweb.vercel.app/)
[![Dataset Status](https://img.shields.io/badge/Cat%C3%A1logo-114%20Glifos%20Aprobados-10b981?style=flat)]()
[![Lexicon Size](https://img.shields.io/badge/L%C3%A9xico%20Coloane-16%2C495%20Palabras-purple?style=flat)]()

---

## 🎯 1. Finalidad del Proyecto

La caligrafía manuscrita de Francisco Coloane posee una riqueza histórica y literaria incalculable, pero presenta complejidades inherentes a la cursiva rápida de pluma fuente: inclinación pronunciada, trazos continuos inter-carácter y ligaduras densas.

El propósito central de este proyecto es **desarrollar un sistema integral de preservación y transcripción digital** mediante un enfoque *Bottom-Up (de abajo hacia arriba)*:

1. **Catalogar la Anatomía Caligráfica:** Descomponer los manuscritos en glifos individuales puros clasificados por posición anatómica (`inicial`, `media`, `final`, `aislada`).
2. **Modelar las Ligaduras y Métricas:** Estudiar la topología del trazo de Coloane mediante esqueletizado 1D, identificando constantes físicas como el avance horizontal promedio ($\Delta x \approx 20.3\text{ px/letra}$).
3. **Síntesis Caligráfica Fidedigna:** Recrear texto inédito y continuo que fluya con la caligrafía real del autor usando curvas Bézier $C^1$ y vectores SVG puros.
4. **Transcripción Asistida (*Human-in-the-Loop*):** Proporcionar una plataforma de reconocimiento óptico asistido que integre visión por computador, morfología zonal y el vocabulario completo de las obras de Coloane para acelerar la transcripción de sus cuadernos y borradores.

---

## 🗺️ 2. Ecosistema de Módulos y Experimentos

El repositorio está organizado en módulos independientes y desacoplados:

| Directorio | Módulo / Experimento | Puerto Local | Estado | Descripción |
| :--- | :--- | :---: | :---: | :--- |
| **`experimentos/06_web_coloane/`** | **Web en Producción (Vercel)** | `8080` | 🟢 Activo | Anotador web colaborativo con buffer en Supabase y sincronización a GitHub. **114 glifos catalogados**. |
| **`experimentos/07_anotador_palabras_ligaduras/`** | **Anotador de Palabras y Ligaduras** | `8085` | 🟢 Activo | Segmentación con polígono multinodo, extracción de esqueletos Zhang-Suen y métricas de enlace. |
| **`experimentos/07_1_sintetizador_frases_cursivas/`** | **Sintetizador Caligráfico Cursivo** | `8086` | 🟢 Activo | Ensamblaje de frases multilínea con puentes Bézier $C^1$ y soporte dual **Vectorial SVG / Raster PNG**. |
| **`experimentos/08_analizador_transcriptor_asistido/`** | **Analizador y Transcriptor Asistido** | `8087` | 🟡 Prototipo | Workbench con soporte <kbd>Ctrl</kbd> + <kbd>V</kbd>, aislamiento de tinta y decodificador léxico de Coloane. |
| **`corpus_coloane_obsidian/`** | **Corpus Digitalizado & Léxico** | — | 📚 Base | Novelas, cuentos y base de datos de frecuencia de **16,495 palabras** de Francisco Coloane. |

---

## 🚀 3. Guía de Ejecución Rápida

### 🌐 Aplicación Web en Producción:
Accede directamente desde cualquier navegador a:  
👉 **[https://coloaneweb.vercel.app/](https://coloaneweb.vercel.app/)**

### 💻 Ejecución Local de los Laboratorios:

* **Experimento 06 (Anotador de Glifos):**
  ```powershell
  python experimentos/06_web_coloane/server_anotador.py
  # Abre: http://localhost:8080
  ```

* **Experimento 07 (Anotador de Palabras y Ligaduras):**
  ```powershell
  python experimentos/07_anotador_palabras_ligaduras/server_anotador_palabras.py
  # Abre: http://localhost:8085
  ```

* **Experimento 07.1 (Sintetizador Caligráfico Cursivo):**
  ```powershell
  python experimentos/07_1_sintetizador_frases_cursivas/server_sintetizador.py
  # Abre: http://localhost:8086
  ```

* **Experimento 08 (Analizador y Transcriptor Asistido):**
  ```powershell
  python experimentos/08_analizador_transcriptor_asistido/server_transcriptor.py
  # Abre: http://localhost:8087
  ```

---

## 📖 4. Documentación Detallada

Para una inmersión técnica completa en la arquitectura, algoritmos y estado de la base de datos, consulta:
* 📄 [**`CONTEXTO_PROYECTO_TRANSCRIPCION_COLOANE.md`**](./CONTEXTO_PROYECTO_TRANSCRIPCION_COLOANE.md): Bitácora técnica y arquitectura completa del ecosistema.
* 📄 [**`GUIA_CARACTERISTICAS_MANUSCRITOS_COLOANE.md`**](./GUIA_CARACTERISTICAS_MANUSCRITOS_COLOANE.md): Guía caligráfica y morfológica de la pluma de Francisco Coloane.

---

## 📜 Licencia y Créditos
* **Autoría & Desarrollo:** Proyecto de investigación caligráfica e Inteligencia Artificial para el patrimonio literario de Francisco Coloane.
* **Fuente de Manuscritos:** *"Escritos y relato desde Quemchi"* (1977) y cuadernos originales de Francisco Coloane.
