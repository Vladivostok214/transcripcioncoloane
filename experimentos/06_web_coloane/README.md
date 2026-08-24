# Experimento 06: Banco & Anotador Web de Glifos (Francisco Coloane)

**Fuente Única Oficial de Verdad del Catálogo Caligráfico**  
Plataforma web colaborativa desplegada en la nube para el acopio continuo, aislamiento morfológico de tinta y catalogación arquetípica de manuscritos del escritor chileno Francisco Coloane (*"Escritos y relato desde Quemchi", 1977*).

---

## 🚀 Acceso en Producción

* **🌐 Aplicación Web en Vivo:** **[https://coloaneweb.vercel.app/](https://coloaneweb.vercel.app/)**
* **📦 Repositorio GitHub:** `Vladivostok214/transcripcioncoloane` (Rama `main`)
* **☁️ Buffer de Acopio:** Supabase (`staging_glyphs` + bucket `staging_crops`)

*(Para levantar un entorno de desarrollo local: ejecuta `python server_anotador.py` y abre `http://localhost:8000`).*

---

## 🎯 Finalidad y Objetivos del Experimento 06

1. **Descentralización y Colaboración:** Permitir que colaboradores externos ingresen desde cualquier computador, carguen capturas de alta resolución (o peguen con `Ctrl + V`) y cataloguen letras manuscritas sin requerir instalaciones de Python ni entornos locales.
2. **Motor de Aislamiento de Tinta en JS Nativo (0.2 ms):** Reproduce en el navegador el algoritmo Gaussiano adaptativo ($C=10$) y apertura morfológica ($2\times 2$) para extraer la tinta pura en formato **RGBA (#F0F0F0 + canal Alfa)** sin fondo de papel.
3. **Pipeline de Curaduría Asíncrona (Buffer $\rightarrow$ Admin $\rightarrow$ GitHub):**
   - Los colaboradores guardan en la nube (Supabase).
   - El administrador (**`Wladimir`**) revisa las muestras desde la **Bandeja de Curaduría** en la web.
   - Con un solo clic en **"🚀 Sincronizar Aprobados a GitHub"**, una función serverless empaqueta los recortes PNG, actualiza los datasets JSON/CSV y genera **un commit limpio en `main`**, limpiando el almacenamiento temporal en Supabase a 0 MB.
4. **Alimentación Continua del Monorepo:** Cualquier actualización en la web se sincroniza a la máquina local mediante `git pull origin main`, nutriendo de inmediato los experimentos de vectorización SVG (`04.2`) y spotting caligráfico (`05`).

---

## 🔄 Flujo de Trabajo y Ciclo de Vida

```
┌─────────────────────────┐
│ Colaboradores en la Web │ -> Ingesta (PNG / Ctrl+V) -> Recorte y Clasificación
└────────────┬────────────┘
             │ (Guardar en Banco de Datos)
             ▼
┌─────────────────────────┐
│   Supabase Cloud Buffer │ -> staging_crops (PNGs) + staging_glyphs (status: 'pendiente')
└────────────┬────────────┘
             │ (Bandeja de Revisión)
             ▼
┌─────────────────────────┐
│  Curaduría Admin Wladi  │ -> Descarte de muestras con ruido / Corrección
└────────────┬────────────┘
             │ (Sincronizar Aprobados a GitHub)
             ▼
┌─────────────────────────┐
│    Vercel Serverless    │ -> api/sync_github.js crea 1 commit en GitHub main
└────────────┬────────────┘    y purga la cola en Supabase
             │
             ▼
┌─────────────────────────┐
│     Tu PC Local (Git)   │ -> 'git pull origin main' actualiza el catálogo maestro
└─────────────────────────┘
```

---

## 📁 Estructura del Experimento

```
experimentos/06_web_coloane/
├── index.html                   # UI Frontend SPA interactiva (Noir-Tech, Canvas 2D, JS Ink Isolation)
├── dataset_glifos_manuales.json # Base de datos maestra oficial de glifos en formato JSON
├── dataset_glifos_manuales.csv  # Base de datos maestra oficial tabular en formato CSV
├── crops/                       # Recortes originales de cada glifo en RGB (300 DPI)
├── crops_isolated/              # Recortes con tinta pura aislada RGBA (#F0F0F0 + Alfa)
├── api/
│   └── sync_github.js           # Función Serverless para Vercel (Consolidación a GitHub)
├── sync_from_supabase.py        # Herramienta CLI de sincronización directa desde terminal
├── setup_supabase.sql           # Script SQL para recrear la tabla y el bucket de Storage
├── vercel.json                  # Configuración de despliegue en Vercel
├── .env.example                 # Variables de entorno requeridas para Vercel
└── server_anotador.py           # Backend HTTP en Python para desarrollo y pruebas locales
```

---

## ⌨️ Atajos de Teclado y Controles

| Tecla / Atajo | Acción |
| :--- | :--- |
| **`Ctrl + V`** | Pegar imagen o captura de pantalla directamente desde el portapapeles. |
| **`1`** | Activar herramienta de selección **Rectangular** (letras limpias). |
| **`2`** | Activar herramienta de selección **Poligonal** (letras cursivas entrelazadas). |
| **`Enter`** | Confirmar clasificación del popover / Cerrar polígono. |
| **`Esc`** | Cancelar selección activa o cerrar modales. |
| **`Ctrl + S`** | Guardar glifos de la captura actual en el banco de datos. |
| **`R`** | Centrar y ajustar el zoom de la imagen en pantalla. |
| **Rueda del mouse** | Zoom in / zoom out dinámico centrado en el cursor. |
| **Clic derecho / central** | Paneo y navegación fluida por el documento. |

---

## 🔗 Integración con Experimentos Posteriores

El catálogo consolidado en `06_web_coloane` es consumido directamente por:
* **`experimentos/04.2_vectorizacion_glifos/`**: Pipeline de conversión de glifos raster RGBA a curvas Bézier y fuentes tipográficas SVG.
* **`experimentos/05_spotting_glifos_interactivo/`**: Motor de búsqueda interactiva (*Word Spotting*) mediante correlación morfológica normalizada (NCC).
