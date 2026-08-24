"""
Script: procesar_corpus_libros.py
==================================
Procesa los 4 libros publicados en PDF de Francisco Coloane, generando:
1. Un Vault de Obsidian estructurado con Frontmatter YAML y wikilinks [[...]].
2. Archivos Markdown completos por libro y archivos individuales por cuento/capítulo.
3. Diccionario léxico, análisis de frecuencias, bi-gramas y tri-gramas para NLP.
"""

import os
import sys
import re
import json
from collections import Counter
import unicodedata

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import fitz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = r"C:\Users\WLADI\Desktop\COLOANE\LIBROS PUBLICADOS"
VAULT_DIR = os.path.join(BASE_DIR, "corpus_coloane_obsidian")

# Carpetas del Vault
DIR_LIBROS_COMPLETOS = os.path.join(VAULT_DIR, "01_libros_completos")
DIR_CUENTOS = os.path.join(VAULT_DIR, "02_cuentos_y_capitulos")
DIR_LEXICO = os.path.join(VAULT_DIR, "03_analisis_lexico")

for d in [VAULT_DIR, DIR_LIBROS_COMPLETOS, DIR_CUENTOS, DIR_LEXICO]:
    os.makedirs(d, exist_ok=True)

def limpiar_texto_pagina(texto):
    """Limpia encabezados, números de página y artefactos de maquetación."""
    lineas = texto.splitlines()
    lineas_limpias = []
    
    for l in lineas:
        l_str = l.strip()
        if not l_str:
            lineas_limpias.append("")
            continue
        # Eliminar pies de página lectulandia / página
        if re.search(r'www\.lectulandia\.com\s*-\s*P[aá]gina\s*\d+', l_str, re.I):
            continue
        if re.match(r'^P[aá]gina\s*\d+$', l_str, re.I):
            continue
        if re.match(r'^\d+$', l_str):
            continue
        if 'Titivillus' in l_str or 'ePub r1.' in l_str or 'ePUB v1.' in l_str:
            continue
        lineas_limpias.append(l_str)
    
    return "\n".join(lineas_limpias)

def unir_parrafos(texto):
    """Une saltos de línea suaves dentro de párrafos y repara guiones de corte."""
    # 1. Unir palabras con guión al final de la línea: 'pa- \n labra' -> 'palabra'
    texto = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)
    
    # 2. Separar por bloques de párrafos
    lineas = texto.splitlines()
    parrafos = []
    parrafo_actual = []
    
    for l in lineas:
        l_strip = l.strip()
        if not l_strip:
            if parrafo_actual:
                parrafos.append(" ".join(parrafo_actual))
                parrafo_actual = []
        else:
            # Si la línea empieza con diálogo o título, separar
            if l_strip.startswith('—') or l_strip.startswith('«') or l_strip.startswith('#'):
                if parrafo_actual:
                    parrafos.append(" ".join(parrafo_actual))
                    parrafo_actual = []
            parrafo_actual.append(l_strip)
            
    if parrafo_actual:
        parrafos.append(" ".join(parrafo_actual))
        
    return "\n\n".join(parrafos)

def extraer_libro_cabo_de_hornos(pdf_path):
    doc = fitz.open(pdf_path)
    # Extraer texto desde página 4
    texto_total = ""
    for i in range(3, len(doc)):
        texto_total += limpiar_texto_pagina(doc[i].get_text()) + "\n"
        
    cuentos_titulos = [
        "Cabo de Hornos", "La voz del viento", "El témpano de Kanasaka",
        "El Flamenco", "El australiano", "El páramo", "Palo al medio",
        "El último contrabando", "El vellonero", "Cururo",
        "El suplicio de agua y luna", "La venganza del mar",
        "La gallina de los huevos de luz"
    ]
    
    # Dividir texto por títulos
    cuentos = []
    for idx, titulo in enumerate(cuentos_titulos):
        patron = re.escape(titulo)
        # Buscar posición
        pos = re.search(r'\n\s*' + patron + r'\s*\n', texto_total)
        if not pos:
            # buscar sin salto
            pos = re.search(patron, texto_total)
            
        pos_inicio = pos.start() if pos else -1
        cuentos.append({
            "titulo": titulo,
            "pos": pos_inicio,
            "idx": idx + 1
        })
        
    cuentos = [c for c in cuentos if c["pos"] != -1]
    cuentos.sort(key=lambda x: x["pos"])
    
    resultado_cuentos = []
    for i in range(len(cuentos)):
        inicio = cuentos[i]["pos"] + len(cuentos[i]["titulo"])
        fin = cuentos[i+1]["pos"] if i + 1 < len(cuentos) else len(texto_total)
        contenido = texto_total[inicio:fin].strip()
        contenido_limpio = unir_parrafos(contenido)
        resultado_cuentos.append({
            "titulo": cuentos[i]["titulo"],
            "numero": i + 1,
            "texto": contenido_limpio
        })
        
    return {
        "titulo_libro": "Cabo de Hornos",
        "slug": "cabo_de_hornos_1941",
        "ano": 1941,
        "genero": "Cuentos",
        "cuentos": resultado_cuentos
    }

def extraer_libro_grumete(pdf_path):
    doc = fitz.open(pdf_path)
    texto_total = ""
    for i in range(3, len(doc)):
        texto_total += limpiar_texto_pagina(doc[i].get_text()) + "\n"
        
    capitulos_titulos = [
        "¡Rumbo al sur!", "Primera noche", "¡El último grumete!",
        "¡Tres bultos a estribor!", "El fantasma del \"Leonora\"",
        "Tempestad mar afuera", "La caza de ballenas", "Los Alacalufes",
        "De Punta Arenas a la \"Tumba del diablo\"", "Detrás de los témpanos",
        "El paraiso de las Nutrias", "La avestruz del mar", "De regreso",
        "La locura de Escobedo"
    ]
    
    capitulos = []
    for idx, titulo in enumerate(capitulos_titulos):
        patron = re.escape(titulo)
        pos = re.search(patron, texto_total)
        pos_inicio = pos.start() if pos else -1
        capitulos.append({
            "titulo": titulo,
            "pos": pos_inicio,
            "idx": idx + 1
        })
        
    capitulos = [c for c in capitulos if c["pos"] != -1]
    capitulos.sort(key=lambda x: x["pos"])
    
    resultado_caps = []
    for i in range(len(capitulos)):
        inicio = capitulos[i]["pos"] + len(capitulos[i]["titulo"])
        fin = capitulos[i+1]["pos"] if i + 1 < len(capitulos) else len(texto_total)
        contenido = texto_total[inicio:fin].strip()
        contenido_limpio = unir_parrafos(contenido)
        resultado_caps.append({
            "titulo": capitulos[i]["titulo"],
            "numero": i + 1,
            "texto": contenido_limpio
        })
        
    return {
        "titulo_libro": "El último grumete de la Baquedano",
        "slug": "el_ultimo_grumete_de_la_baquedano_1941",
        "ano": 1941,
        "genero": "Novela",
        "cuentos": resultado_caps
    }

def extraer_libro_tierra_del_fuego(pdf_path):
    doc = fitz.open(pdf_path)
    texto_total = ""
    for i in range(4, len(doc)):
        texto_total += limpiar_texto_pagina(doc[i].get_text()) + "\n"
        
    # Títulos y letras iniciales de drop-cap
    titulos = [
        ("Tierra del Fuego", "L"),
        ("En el caballo de la aurora", "P"),
        ("De cómo murió el chilote Otey", "A"),
        ("Cinco marineros y un ataúd verde", "U"),
        ("Tierra de olvido", "A"),
        ("Témpano sumergido", "U"),
        ("La botella de caña", "D"),
        ("El constructor del faro", "E")
    ]
    
    cuentos = []
    for idx, (titulo, let) in enumerate(titulos):
        patron = re.escape(titulo)
        pos = re.search(patron, texto_total)
        pos_inicio = pos.start() if pos else -1
        cuentos.append({
            "titulo": titulo,
            "letra_drop": let,
            "pos": pos_inicio,
            "idx": idx + 1
        })
        
    cuentos = [c for c in cuentos if c["pos"] != -1]
    cuentos.sort(key=lambda x: x["pos"])
    
    resultado_cuentos = []
    for i in range(len(cuentos)):
        inicio = cuentos[i]["pos"] + len(cuentos[i]["titulo"])
        fin = cuentos[i+1]["pos"] if i + 1 < len(cuentos) else len(texto_total)
        contenido = texto_total[inicio:fin].strip()
        
        # Restaurar letra de inicio si fue aislada
        drop = cuentos[i]["letra_drop"]
        if contenido and not contenido.startswith(drop):
            contenido = drop + contenido
            
        contenido_limpio = unir_parrafos(contenido)
        resultado_cuentos.append({
            "titulo": cuentos[i]["titulo"],
            "numero": i + 1,
            "texto": contenido_limpio
        })
        
    return {
        "titulo_libro": "Tierra del Fuego",
        "slug": "tierra_del_fuego_1956",
        "ano": 1956,
        "genero": "Cuentos",
        "cuentos": resultado_cuentos
    }

def extraer_libro_chilote_otey(pdf_path):
    doc = fitz.open(pdf_path)
    # Extraer texto desde página 4 (después de la portada)
    texto_total = ""
    for i in range(4, len(doc)):
        texto_total += limpiar_texto_pagina(doc[i].get_text()) + "\n"
        
    titulos = [
        "Prólogo", "El chilote Otey", "Viniendo de los corrales",
        "La botella de caña", "Témpano sumergido", "Tierra del Fuego",
        "Cinco marineros y un ataúd verde", "Rumbo a Puerto Edén",
        "Golfo de Penas", "Cabo de Hornos", "El témpano de Kanasaka",
        "Tierra de olvido", "VOCABULARIO REGIONAL"
    ]
    
    cuentos = []
    # Buscar cada título asegurando que aparezca como línea de encabezado
    for idx, titulo in enumerate(titulos):
        patron = r'(?:^|\n)\s*' + re.escape(titulo) + r'\s*(?:\n|$)'
        matches = list(re.finditer(patron, texto_total))
        if matches:
            # Tomar el primer match que no sea el título del libro en portada
            pos = matches[0].start()
            cuentos.append({
                "titulo": titulo,
                "pos": pos,
                "idx": idx + 1
            })
        
    cuentos = [c for c in cuentos if c["pos"] != -1]
    cuentos.sort(key=lambda x: x["pos"])
    
    resultado_cuentos = []
    for i in range(len(cuentos)):
        inicio = cuentos[i]["pos"] + len(cuentos[i]["titulo"])
        fin = cuentos[i+1]["pos"] if i + 1 < len(cuentos) else len(texto_total)
        contenido = texto_total[inicio:fin].strip()
        contenido_limpio = unir_parrafos(contenido)
        resultado_cuentos.append({
            "titulo": cuentos[i]["titulo"],
            "numero": i + 1,
            "texto": contenido_limpio
        })
        
    return {
        "titulo_libro": "El chilote Otey y otros relatos",
        "slug": "el_chilote_otey_y_otros_relatos_1971",
        "ano": 1971,
        "genero": "Antología y Relatos",
        "cuentos": resultado_cuentos
    }

def tokenizar_palabras(texto):
    """Extrae palabras limpias conservando tildes y eñes."""
    palabras = re.findall(r'[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]+', texto)
    return [p.lower() for p in palabras]

def procesar_todo():
    print("=" * 70)
    print("  CONSTRUCTOR DEL CORPUS OBSIDIAN & ANALIZADOR LÉXICO (COLOANE)")
    print("=" * 70)
    
    libros = []
    
    # 1. Cabo de Hornos
    f_cabo = os.path.join(PDF_DIR, "Cabo de Hornos - Francisco Coloane.pdf")
    if os.path.exists(f_cabo):
        print("📖 Procesando 'Cabo de Hornos (1941)'...")
        libros.append(extraer_libro_cabo_de_hornos(f_cabo))
        
    # 2. El último grumete
    f_grumete = os.path.join(PDF_DIR, "El ultimo grumete de la Baqueda - Francisco Coloane.pdf")
    if os.path.exists(f_grumete):
        print("📖 Procesando 'El último grumete de la Baquedano (1941)'...")
        libros.append(extraer_libro_grumete(f_grumete))
        
    # 3. Tierra del Fuego
    f_tierra = os.path.join(PDF_DIR, "Tierra del fuego - Francisco Coloane.pdf")
    if os.path.exists(f_tierra):
        print("📖 Procesando 'Tierra del Fuego (1956)'...")
        libros.append(extraer_libro_tierra_del_fuego(f_tierra))
        
    # 4. El chilote Otey
    f_otey = os.path.join(PDF_DIR, "El chilote Otey y otros relatos - Francisco Coloane.pdf")
    if os.path.exists(f_otey):
        print("📖 Procesando 'El chilote Otey y otros relatos (1971)'...")
        libros.append(extraer_libro_chilote_otey(f_otey))
        
    # Variables globales para análisis léxico
    todas_las_palabras = []
    total_palabras_corpus = 0
    vocabulario_regional_texto = ""
    
    indice_general_md = [
        "# 📚 Corpus Literario Francisco Coloane (Vault de Obsidian)",
        "",
        "Bienvenido al **Vault de Conocimiento y Análisis Lingüístico** de la obra narrativa de **Francisco Coloane**.",
        "Este corpus contiene las obras digitalizadas en texto claro, estructuradas con enlaces bidireccionales `[[...]]` para análisis filológico, extracción de entidades y entrenamiento de modelos de IA para manuscritos.",
        "",
        "---",
        "",
        "## 📖 Libros Publicados",
        ""
    ]
    
    for l_idx, libro in enumerate(libros, 1):
        slug_libro = libro["slug"]
        subcarpeta_cuentos = os.path.join(DIR_CUENTOS, slug_libro)
        os.makedirs(subcarpeta_cuentos, exist_ok=True)
        
        texto_completo_libro = []
        links_cuentos = []
        total_palabras_libro = 0
        
        print(f"\n📂 Generando notas para '{libro['titulo_libro']}' ({len(libro['cuentos'])} secciones/cuentos)...")
        
        for c in libro["cuentos"]:
            titulo_limpio = c["titulo"].replace('"', '').replace('«', '').replace('»', '').strip()
            slug_cuento = f"{c['numero']:02d}_{re.sub(r'[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ]+', '_', titulo_limpio).strip('_')}"
            
            palabras_cuento = tokenizar_palabras(c["texto"])
            num_palabras = len(palabras_cuento)
            total_palabras_libro += num_palabras
            todas_las_palabras.extend(palabras_cuento)
            
            if "VOCABULARIO REGIONAL" in titulo_limpio.upper():
                vocabulario_regional_texto = c["texto"]
                
            # Archivo de cuento individual
            md_cuento = f"""---
titulo: "{titulo_limpio}"
libro: "{libro['titulo_libro']}"
ano: {libro['ano']}
genero: "{libro['genero']}"
numero_orden: {c['numero']}
total_palabras: {num_palabras}
tags:
  - coloane
  - {libro['genero'].lower().replace(' ', '_')}
  - literatura_chilena
---

# {c['titulo']}
*Parte de [[{libro['titulo_libro']}]] ({libro['ano']})*

**Métricas:** {num_palabras:,} palabras | **Género:** {libro['genero']}

---

{c['texto']}

---
*Volver al libro: [[{libro['titulo_libro']}]] | [[00_INDICE_GENERAL|Índice General]]*
"""
            path_cuento = os.path.join(subcarpeta_cuentos, f"{slug_cuento}.md")
            with open(path_cuento, "w", encoding="utf-8") as f:
                f.write(md_cuento)
                
            links_cuentos.append(f"- [[{slug_cuento}|{c['numero']:02d}. {titulo_limpio}]] ({num_palabras:,} palabras)")
            texto_completo_libro.append(f"## {c['titulo']}\n\n{c['texto']}")
            
        total_palabras_corpus += total_palabras_libro
        
        # Archivo de libro completo
        md_libro = f"""---
titulo: "{libro['titulo_libro']}"
autor: "Francisco Coloane"
ano_publicacion: {libro['ano']}
genero: "{libro['genero']}"
total_secciones: {len(libro['cuentos'])}
total_palabras: {total_palabras_libro}
tags:
  - coloane
  - libro_completo
  - {libro['genero'].lower().replace(' ', '_')}
---

# 📖 {libro['titulo_libro']} ({libro['ano']})
**Autor:** Francisco Coloane | **Total Palabras:** {total_palabras_libro:,}

---

## 📑 Índice de Cuentos y Capítulos
{chr(10).join(links_cuentos)}

---

# Texto Completo de la Obra

{chr(10).join(texto_completo_libro)}

---
*[[00_INDICE_GENERAL|Volver al Índice General del Corpus]]*
"""
        path_libro = os.path.join(DIR_LIBROS_COMPLETOS, f"{slug_libro}.md")
        with open(path_libro, "w", encoding="utf-8") as f:
            f.write(md_libro)
            
        indice_general_md.append(f"### {l_idx}. [[{slug_libro}|{libro['titulo_libro']} ({libro['ano']})]]")
        indice_general_md.append(f"- **Género:** {libro['genero']} | **Secciones:** {len(libro['cuentos'])} | **Total Palabras:** {total_palabras_libro:,}")
        indice_general_md.extend([f"  {link}" for link in links_cuentos[:5]])
        if len(links_cuentos) > 5:
            indice_general_md.append(f"  - *(y {len(links_cuentos)-5} cuentos/capítulos más...)*")
        indice_general_md.append("")
        
    # Guardar Índice General
    indice_general_md.extend([
        "---",
        "",
        "## 🔬 Herramientas de Análisis Léxico & NLP",
        "",
        "- [[03_analisis_lexico/informe_estadistico_corpus|📊 Informe Estadístico y Métricas del Corpus]]",
        "- [[03_analisis_lexico/vocabulario_regional_maritimo|⚓ Vocabulario Regional y Marítimo]]",
        "- `03_analisis_lexico/coloane_lexicon_frecuencias.json` (Diccionario completo de frecuencias)",
        "- `03_analisis_lexico/coloane_bigramas_frecuentes.json` (Colocaciones de 2 palabras)",
        "- `03_analisis_lexico/coloane_trigramas_frecuentes.json` (Colocaciones de 3 palabras)",
        "",
        "---",
        "*Corpus generado automáticamente para el proyecto TRANSCRIPCIONES COLOANE.*"
    ])
    
    with open(os.path.join(VAULT_DIR, "00_INDICE_GENERAL.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(indice_general_md))
        
    # 2. Análisis Estadístico y Léxico
    print("\n🔬 Calculando estadísticas léxicas, frecuencias de palabras y n-gramas...")
    conteo_palabras = Counter(todas_las_palabras)
    vocabulario_unico = len(conteo_palabras)
    
    # Bi-gramas y Tri-gramas
    bigramas = Counter()
    trigramas = Counter()
    for i in range(len(todas_las_palabras) - 1):
        bigramas[f"{todas_las_palabras[i]} {todas_las_palabras[i+1]}"] += 1
    for i in range(len(todas_las_palabras) - 2):
        trigramas[f"{todas_las_palabras[i]} {todas_las_palabras[i+1]} {todas_las_palabras[i+2]}"] += 1
        
    # Guardar JSONs
    with open(os.path.join(DIR_LEXICO, "coloane_lexicon_frecuencias.json"), "w", encoding="utf-8") as f:
        json.dump(dict(conteo_palabras.most_common()), f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(DIR_LEXICO, "coloane_bigramas_frecuentes.json"), "w", encoding="utf-8") as f:
        json.dump(dict(bigramas.most_common(1000)), f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(DIR_LEXICO, "coloane_trigramas_frecuentes.json"), "w", encoding="utf-8") as f:
        json.dump(dict(trigramas.most_common(1000)), f, ensure_ascii=False, indent=2)
        
    # Filtrar palabras de interés náutico / patagónico
    terminos_clave = [
        "mar", "viento", "isla", "ola", "olas", "barco", "agua", "aguas", "nieve", "cúter", "faro", "lobo", "lobos",
        "ballena", "ballenas", "marineros", "cabo", "tierra", "fuego", "punta", "arenas", "canal", "canales",
        "bahía", "embarcación", "bote", "pescado", "cielo", "noche", "sombras", "muerte", "perro", "perros",
        "caballo", "caballos", "oro", "guanaco", "albatros", "petrel", "chubascos", "temporal", "temporales",
        "navegación", "sur", "babor", "estribor", "proa", "popa", "travesía", "quemchi", "chilote", "otey"
    ]
    
    top_tematicos = []
    for term in terminos_clave:
        if term in conteo_palabras:
            top_tematicos.append((term, conteo_palabras[term]))
    top_tematicos.sort(key=lambda x: x[1], reverse=True)
    
    # Informe Estadístico en Markdown
    informe_md = f"""# 📊 Informe Estadístico del Corpus Literario de Francisco Coloane

Este documento sintetiza las propiedades cuantitativas y léxicas del corpus compuesto por 4 obras maestras de Francisco Coloane.

---

## 📈 Resumen Cuantitativo General

| Métrica | Valor |
| :--- | :--- |
| **Obras Digitalizadas** | 4 libros completos |
| **Total de Cuentos / Capítulos** | {sum(len(l['cuentos']) for l in libros)} secciones independientes |
| **Total de Palabras Procesadas** | **{total_palabras_corpus:,} palabras** |
| **Vocabulario Único (Palabras Distintas)** | **{vocabulario_unico:,} palabras únicas** |
| **Densidad Léxica (*Type-Token Ratio*)** | **{(vocabulario_unico / total_palabras_corpus)*100:.2f}%** |

---

## 📖 Desglose por Obra

| Obra | Año | Género | Secciones | Total Palabras |
| :--- | :--- | :--- | :--- | :--- |
{chr(10).join([f"| [[{l['slug']}|{l['titulo_libro']}]] | {l['ano']} | {l['genero']} | {len(l['cuentos'])} | {sum(len(tokenizar_palabras(c['texto'])) for c in l['cuentos']):,} |" for l in libros])}

---

## ⚓ Términos Temáticos y Náuticos Más Frecuentes

Estos términos representan el núcleo del universo narrativo de Coloane y servirán como pesos prioritarios para la decodificación en modelos de IA:

| Término | Frecuencia Absoluta | Contexto Primario |
| :--- | :--- | :--- |
{chr(10).join([f"| **{t[0]}** | {t[1]:,} ocurrencias | Término fundamental del idiolecto austral |" for t in top_tematicos[:25]])}

---

## 🔗 N-Gramos y Colocaciones Típicas (Muestras)

Colocaciones recurrentes en la prosa de Coloane:

1. `tierra del fuego` ({trigramas.get('tierra del fuego', 0)} veces)
2. `cabo de hornos` ({trigramas.get('cabo de hornos', 0)} veces)
3. `punta arenas` ({bigramas.get('punta arenas', 0)} veces)
4. `mar afuera` ({bigramas.get('mar afuera', 0)} veces)
5. `mar adentro` ({bigramas.get('mar adentro', 0)} veces)
6. `lobos marinos` ({bigramas.get('lobos marinos', 0)} veces)
7. `golfo de penas` ({trigramas.get('golfo de penas', 0)} veces)
8. `canal beagle` ({bigramas.get('canal beagle', 0)} veces)
9. `isla de` ({bigramas.get('isla de', 0)} veces)
10. `a través de` ({trigramas.get('a través de', 0)} veces)

---

## 🎯 Aplicación en el Reconocimiento de Manuscritos (HTR)

1. **Corrección Ortográfica Dirigida:** El diccionario `coloane_lexicon_frecuencias.json` evita que el transcriptor confunda toponimia o jerga marina con palabras comunes.
2. **Modelado de Lenguaje N-Gram:** Los modelos de decodificación beam-search usarán estas probabilidades para desempatar letras confusas en los manuscritos.
3. **Síntesis Realista de Páginas (Exp 07):** El generador sintético tomará oraciones reales de este corpus para componer páginas con caligrafía idéntica a la real.
"""
    with open(os.path.join(DIR_LEXICO, "informe_estadistico_corpus.md"), "w", encoding="utf-8") as f:
        f.write(informe_md)
        
    # Vocabulario Regional extraído
    if vocabulario_regional_texto:
        with open(os.path.join(DIR_LEXICO, "vocabulario_regional_maritimo.md"), "w", encoding="utf-8") as f:
            f.write(f"# ⚓ Vocabulario Regional y Marítimo de Francisco Coloane\n\n*Extraído directamente de la edición de 'El chilote Otey y otros relatos' (Quimantú, 1971)*\n\n---\n\n{vocabulario_regional_texto}")
            
    print("\n🎉 ¡Procesamiento completado con éxito total!")
    print(f"   Total Palabras: {total_palabras_corpus:,}")
    print(f"   Vocabulario Único: {vocabulario_unico:,} palabras")
    print(f"   Vault creado en: {VAULT_DIR}")

if __name__ == '__main__':
    procesar_todo()
