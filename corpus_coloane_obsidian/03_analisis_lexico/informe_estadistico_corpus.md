# 📊 Informe Estadístico del Corpus Literario de Francisco Coloane

Este documento sintetiza las propiedades cuantitativas y léxicas del corpus compuesto por 4 obras maestras de Francisco Coloane.

---

## 📈 Resumen Cuantitativo General

| Métrica | Valor |
| :--- | :--- |
| **Obras Digitalizadas** | 4 libros completos |
| **Total de Cuentos / Capítulos** | 48 secciones independientes |
| **Total de Palabras Procesadas** | **174,305 palabras** |
| **Vocabulario Único (Palabras Distintas)** | **16,495 palabras únicas** |
| **Densidad Léxica (*Type-Token Ratio*)** | **9.46%** |

---

## 📖 Desglose por Obra

| Obra | Año | Género | Secciones | Total Palabras |
| :--- | :--- | :--- | :--- | :--- |
| [[cabo_de_hornos_1941|Cabo de Hornos]] | 1941 | Cuentos | 13 | 46,580 |
| [[el_ultimo_grumete_de_la_baquedano_1941|El último grumete de la Baquedano]] | 1941 | Novela | 14 | 21,696 |
| [[tierra_del_fuego_1956|Tierra del Fuego]] | 1956 | Cuentos | 8 | 50,195 |
| [[el_chilote_otey_y_otros_relatos_1971|El chilote Otey y otros relatos]] | 1971 | Antología y Relatos | 13 | 55,834 |

---

## ⚓ Términos Temáticos y Náuticos Más Frecuentes

Estos términos representan el núcleo del universo narrativo de Coloane y servirán como pesos prioritarios para la decodificación en modelos de IA:

| Término | Frecuencia Absoluta | Contexto Primario |
| :--- | :--- | :--- |
| **mar** | 431 ocurrencias | Término fundamental del idiolecto austral |
| **tierra** | 261 ocurrencias | Término fundamental del idiolecto austral |
| **noche** | 254 ocurrencias | Término fundamental del idiolecto austral |
| **viento** | 195 ocurrencias | Término fundamental del idiolecto austral |
| **caballo** | 183 ocurrencias | Término fundamental del idiolecto austral |
| **oro** | 171 ocurrencias | Término fundamental del idiolecto austral |
| **fuego** | 145 ocurrencias | Término fundamental del idiolecto austral |
| **agua** | 128 ocurrencias | Término fundamental del idiolecto austral |
| **cabo** | 127 ocurrencias | Término fundamental del idiolecto austral |
| **isla** | 120 ocurrencias | Término fundamental del idiolecto austral |
| **perro** | 118 ocurrencias | Término fundamental del idiolecto austral |
| **barco** | 116 ocurrencias | Término fundamental del idiolecto austral |
| **nieve** | 115 ocurrencias | Término fundamental del idiolecto austral |
| **cielo** | 98 ocurrencias | Término fundamental del idiolecto austral |
| **aguas** | 96 ocurrencias | Término fundamental del idiolecto austral |
| **canal** | 88 ocurrencias | Término fundamental del idiolecto austral |
| **punta** | 85 ocurrencias | Término fundamental del idiolecto austral |
| **lobo** | 84 ocurrencias | Término fundamental del idiolecto austral |
| **sombras** | 81 ocurrencias | Término fundamental del idiolecto austral |
| **caballos** | 80 ocurrencias | Término fundamental del idiolecto austral |
| **sur** | 79 ocurrencias | Término fundamental del idiolecto austral |
| **olas** | 72 ocurrencias | Término fundamental del idiolecto austral |
| **muerte** | 69 ocurrencias | Término fundamental del idiolecto austral |
| **arenas** | 60 ocurrencias | Término fundamental del idiolecto austral |
| **marineros** | 58 ocurrencias | Término fundamental del idiolecto austral |

---

## 🔗 N-Gramos y Colocaciones Típicas (Muestras)

Colocaciones recurrentes en la prosa de Coloane:

1. `tierra del fuego` (100 veces)
2. `cabo de hornos` (32 veces)
3. `punta arenas` (52 veces)
4. `mar afuera` (18 veces)
5. `mar adentro` (9 veces)
6. `lobos marinos` (2 veces)
7. `golfo de penas` (26 veces)
8. `canal beagle` (22 veces)
9. `isla de` (11 veces)
10. `a través de` (30 veces)

---

## 🎯 Aplicación en el Reconocimiento de Manuscritos (HTR)

1. **Corrección Ortográfica Dirigida:** El diccionario `coloane_lexicon_frecuencias.json` evita que el transcriptor confunda toponimia o jerga marina con palabras comunes.
2. **Modelado de Lenguaje N-Gram:** Los modelos de decodificación beam-search usarán estas probabilidades para desempatar letras confusas en los manuscritos.
3. **Síntesis Realista de Páginas (Exp 07):** El generador sintético tomará oraciones reales de este corpus para componer páginas con caligrafía idéntica a la real.
