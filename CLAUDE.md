# Directrices del Proyecto — Cascadas de Chile

## Contexto del Proyecto

**IMPORTANTE**: Antes de cualquier acción, leer `CONTEXTO_PROYECTO.md` para entender:
- La estrategia SEO y Topical Map del sitio
- Los topical borders (qué contenido crear y cuál NO)
- Las reglas de internal linking
- La guía de estilo y tono
- Las keywords por página
- La priorización de contenido

> **Dominio:** cascadasdechile.cl
> **Stack:** Astro 5 + Tailwind CSS 4
> **Deploy:** GitHub Pages (CI/CD con GitHub Actions)

---

## Herramientas y Agentes Disponibles

### Agentes (`.claude/agents/`)

| Agente | Propósito | Estado |
|--------|-----------|--------|
| `chile-waterfalls-researcher` | Investiga exhaustivamente cascadas chilenas: coordenadas, actividades, alojamiento, flora/fauna, historia, servicios. Entrega JSON estructurado | ✅ |
| `blog-post-publisher` | Crea y publica artículos de blog en el source correcto | ❌ Pendiente |
| `astro-project-navigator` | Guía sobre dónde ubicar archivos en el proyecto Astro | ❌ Pendiente |
| `code-cleanup-analyzer` | Detecta archivos muertos, imports no usados, deps innecesarias | ✅ (user-level) |

### Skills (`.claude/skills/` o user-level)

| Skill | Propósito | Estado |
|-------|-----------|--------|
| `search-intent-analyzer` | Analiza la intención de búsqueda con datos SERP, entropía y competidores | ✅ |
| `content-curation` | Curación SEO de contenido existente (17 pasos) | ✅ |
| `interlinking-strategy` | Genera estrategias de internal linking desde GSC | ✅ |
| `topical-map-builder` | Construye topical maps completos para estrategia SEO semántica | ✅ |
| `seo-project-claude-md` | Genera CLAUDE.md para proyectos SEO | ✅ |
| `voice-cloning-framework` | Replica la voz y tono de marca del autor | ❌ Pendiente |
| `geo-landing-generator` | Genera landings geolocalizadas desde un template | ❌ Pendiente |

### MCP Servers activos

| MCP | Herramientas clave |
|-----|-------------------|
| `dfs-kwr` | `KeywordSuggestions`, `KwsRelacionadas`, `SerpResultados`, `TopicalAuthority`, `RankedKeywordsGeneral` |
| `chrome-devtools` | `navigate_page`, `take_snapshot`, `take_screenshot` |
| `mcp-sql` | Consultas sobre datos de Google Search Console |
| `mcp-ents` | `AnalizarEntidades` — análisis NLP de entidades para SEO |
| `clarity` | `query-analytics-dashboard`, `list-session-recordings` — Microsoft Clarity |
| `analytics-mcp` | `run_report`, `run_realtime_report` — Google Analytics 4 |

---

## Flujos de Trabajo Obligatorios

### REGLA DE ORO: Investigación antes de redacción

**SIEMPRE** que se necesite crear o actualizar contenido de una cascada:

1. **Primero**: Lanzar el agente `chile-waterfalls-researcher` para obtener datos verificados
2. **Segundo**: Ejecutar `search-intent-analyzer` con la keyword objetivo para analizar SERP y competidores
3. **Tercero**: Redactar el contenido usando los datos del researcher + el análisis de intención
4. **NUNCA** inventar datos, coordenadas, precios, nombres de alojamientos o servicios sin verificación

Esta regla aplica para:
- Crear nuevas páginas de cascadas
- Actualizar páginas existentes
- Crear artículos de blog sobre cascadas específicas
- Cualquier contenido que mencione datos factuales de una cascada

---

### 1. Crear Página de Cascada (Template Programmatic SEO)

Seguir estos pasos **en orden secuencial**:

#### Paso 1: Research con agente investigador
Agente: `chile-waterfalls-researcher`
- Investigar TODOS los datos requeridos por el template
- El agente entrega JSON estructurado con: coordenadas, actividades, alojamiento, flora/fauna, historia, clima, seguridad, gastronomía, FAQ
- **No avanzar hasta tener los datos verificados**

#### Paso 2: Research SEO con DataForSEO
Ejecutar en paralelo con `dfs-kwr`:
- `KeywordSuggestions` → keywords relacionadas y long-tail
- `KwsRelacionadas` → co-ocurrencia semántica
- `SerpResultados` → SERP features, AI Overview, URLs que rankean

#### Paso 3: Análisis de competidores
Con MCP `chrome-devtools`:
- Entrar a los top 3-5 resultados orgánicos
- `take_snapshot` → extraer estructura H2s, formato, FAQs, CTAs
- Analizar qué tienen en común los que rankean

#### Paso 4: Análisis de intención de búsqueda
Skill: `search-intent-analyzer`
- Usar con toda la data de pasos 2 y 3
- Clasifica intent, content type ganador, estructura ideal
- Define las secciones obligatorias y entidades que deben aparecer

#### Paso 5: Imágenes reales desde Wikimedia
- Seguir el flujo de la sección "8. Imágenes reales desde Wikimedia Commons"
- Buscar 5 fotos reales (1 hero + 4 galería) con licencia CC en Wikimedia Commons
- Descargar y convertir a WebP con `scripts/download-wikimedia.sh`
- Guardar en `public/assets/cascadas/{slug}/`
- Registrar atribución (autor + licencia) para el campo `galeriaCreditos`
- **No avanzar al paso siguiente sin imágenes reales**

#### Paso 6: Construir la página
- Usar el template de `src/pages/cascadas/salto-del-laja.astro` como referencia
- Poblar el objeto `cascada` con los datos del researcher (Paso 1)
- Incorporar los `consensus_terms` del análisis de entropía como entidades obligatorias
- Respetar las 15 secciones del template:
  1. Hero
  2. Ficha Rápida (8 stats)
  3. Descripción
  4. Cómo Llegar + Mapa OpenStreetMap
  5. Qué Hacer (actividades)
  6. Flora y Fauna
  7. Clima
  8. Historia y Cultura
  9. Seguridad y Recomendaciones
  10. Gastronomía Regional
  11. Dónde Alojarse
  12. Galería
  13. FAQ (con schema FAQPage)
  14. Cascadas Cercanas
  15. CTA Mapa
- **NO puede faltar NINGUNA sección**. Si el researcher no encontró datos para una sección, investigar más o marcar claramente qué falta.

#### Paso 7: Structured Data
Cada página de cascada DEBE incluir JSON-LD:
- `TouristAttraction` con coordenadas reales
- `FAQPage` con las preguntas relevantes
- `BreadcrumbList`

#### Paso 8: Agregar al listado de cascadas
- **OBLIGATORIO**: Agregar la nueva cascada al array `cascadas` en `src/pages/cascadas/index.astro`
- Incluir: `nombre`, `slug`, `region`, `altura`, `dificultad`, `img` (ruta hero), `imgAlt`
- Si la dificultad no existe en `dificultadColor`, agregar la entrada correspondiente

#### Paso 9: Build y verificación
- Ejecutar `npm run build`
- Verificar que la página renderiza correctamente
- Confirmar JSON-LD en el `<head>`
- Verificar que la cascada aparece en el listado `/cascadas`

---

### 2. Crear Artículo de Blog (Pipeline Completo)

#### Paso 1: Selección de keyword
- Elegir del listado pendiente en `CONTEXTO_PROYECTO.md`
- Confirmar con el usuario antes de avanzar

#### Paso 2: Research con DataForSEO
Ejecutar en paralelo con `dfs-kwr`:
- `KeywordSuggestions` → keywords relacionadas y long-tail
- `KwsRelacionadas` → co-ocurrencia semántica
- `SerpResultados` → SERP features, URLs que rankean

#### Paso 3: Análisis de competidores
Con MCP `chrome-devtools`:
- Entrar a los top 3-5 resultados orgánicos
- `take_snapshot` → extraer estructura, formato, FAQs

#### Paso 4: Análisis de intención de búsqueda
Skill: `search-intent-analyzer`

#### Paso 5: Si el artículo menciona cascadas específicas
**OBLIGATORIO**: Lanzar `chile-waterfalls-researcher` para datos verificados

#### Paso 6: Escritura del artículo
Agente: `blog-post-publisher` (cuando esté creado)
- Los `consensus_terms` del análisis de entropía son **obligatorios** en el contenido
- Internal links (mín. 2 a páginas de cascadas o hubs)
- Ejecutar `npm run build`

#### Paso 7: Generación de imágenes (condicional)
Solo si la intención requiere imágenes explicativas:
```bash
python scripts/image-gen/generate.py --prompt "descripcion" --output public/assets/blog/{slug}/nombre.webp
```
- Confirmar con el usuario antes de generar

---

### 3. Curación de Contenido Existente

Usar skill `content-curation` cuando:
- Una página pierde tráfico o rankings
- El contenido tiene más de 6 meses sin actualizar
- El usuario pide "mejorar" o "actualizar" una URL específica

**Regla**: Si la curación afecta datos factuales de cascadas, lanzar primero `chile-waterfalls-researcher` para actualizar los datos.

---

### 4. Analizar Competidores

Usar MCP `chrome-devtools` cuando:
- Se necesita ver estructura de páginas de competidores
- Capturar screenshots para análisis UX/contenido
- Extraer datos estructurados de páginas que rankean

---

### 5. Limpiar Código

Agente: `code-cleanup-analyzer`
- Análisis conservador con backup antes de eliminar
- Detecta: archivos no usados, código muerto, dependencias no utilizadas

---

### 6. Generar Imágenes con IA

```bash
# Generación básica (rápido)
python scripts/image-gen/generate.py --prompt "descripcion" --output public/assets/ruta/nombre.webp

# Pro + 4K
python scripts/image-gen/generate.py --prompt "descripcion" --model pro --image-size 4K --aspect-ratio 16:9

# Editar imagen existente
python scripts/image-gen/generate.py --prompt "instrucciones de edicion" --edit ruta/original.webp
```

Convenciones de ruta:
- Cascadas: `public/assets/cascadas/{slug}/nombre.webp`
- Blog: `public/assets/blog/{slug}/nombre.webp`
- OG images: `public/assets/og/nombre.webp`

---

### 7. Análisis de Entropía SEO

```bash
python scripts/seo-entropy/analyze.py
```
- Analiza la distribución de términos en competidores
- Identifica `consensus_terms` (obligatorios) y `opportunity_terms` (diferenciadores)
- Los `consensus_terms` DEBEN aparecer en el contenido final

---

### 8. Imágenes reales desde Wikimedia Commons

Todas las páginas de cascadas usan **fotos reales** descargadas de Wikimedia Commons. **Nunca usar imágenes placeholder de Unsplash u otros stocks genéricos.**

#### Flujo para obtener imágenes de una cascada nueva

1. **Buscar en Wikimedia Commons API**:
```bash
curl -s -A "CascadasDeChile/1.0" \
  "https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=NOMBRE+CASCADA&srnamespace=6&srlimit=10&format=json"
```

2. **Obtener URLs e info de licencia**:
```bash
curl -s -A "CascadasDeChile/1.0" \
  "https://commons.wikimedia.org/w/api.php?action=query&titles=File:NOMBRE.jpg&prop=imageinfo&iiprop=url|size|extmetadata&format=json"
```

3. **Descargar y convertir con el script**:
```bash
# Hero (1600px ancho)
scripts/download-wikimedia.sh "URL_WIKIMEDIA" "public/assets/cascadas/{slug}/hero.webp" 1600

# Galería (800px ancho)
scripts/download-wikimedia.sh "URL_WIKIMEDIA" "public/assets/cascadas/{slug}/galeria-1.webp" 800
```

4. **Se necesitan 5 imágenes por cascada**: 1 hero + 4 galería
5. **Si no hay suficientes fotos en Wikimedia**: buscar con términos alternativos (nombre del río, región, términos en inglés). Si aún no hay suficientes, notificar al usuario.

#### Licencias aceptables
- **CC0** (dominio público) — no requiere atribución
- **CC BY** — requiere atribución del autor
- **CC BY-SA** — requiere atribución + misma licencia
- **Public domain** — no requiere atribución

#### Atribución obligatoria
Cada página incluye un bloque `galeriaCreditos` con autor, licencia y URL. Se renderiza debajo de la galería con estilo discreto.

#### Estructura de archivos
```
public/assets/cascadas/{slug}/
├── hero.webp        # 1600px ancho, < 500KB
├── galeria-1.webp   # 800px ancho, < 200KB
├── galeria-2.webp
├── galeria-3.webp
└── galeria-4.webp
```

#### Formato del objeto `cascada` para imágenes
```javascript
imagen: '/assets/cascadas/{slug}/hero.webp',
imagenAlt: 'Descripción visual de la imagen hero',
galeria: [
  { src: '/assets/cascadas/{slug}/galeria-1.webp', alt: 'Descripción de la foto 1' },
  { src: '/assets/cascadas/{slug}/galeria-2.webp', alt: 'Descripción de la foto 2' },
  { src: '/assets/cascadas/{slug}/galeria-3.webp', alt: 'Descripción de la foto 3' },
  { src: '/assets/cascadas/{slug}/galeria-4.webp', alt: 'Descripción de la foto 4' },
],
galeriaCreditos: [
  { autor: 'Nombre', licencia: 'CC BY-SA 4.0', url: 'https://commons.wikimedia.org/wiki/File:...' },
],
```

#### Reglas de SEO para imágenes
- Hero usa `<img>` con `fetchpriority="high"` y `decoding="async"` (NO lazy)
- Galería usa `<img>` con `loading="lazy"` y `decoding="async"`
- **Nunca usar `background-image` en CSS** — siempre `<img>` para indexación en Google Images
- Cada imagen DEBE tener `alt` descriptivo y único
- OG image debe ser URL absoluta: `https://cascadasdechile.cl/assets/cascadas/{slug}/hero.webp`
- Structured data `image` también debe ser URL absoluta

---

## Deploy e Infraestructura

### GitHub Pages

- **Site URL**: `https://cascadasdechile.cl`
- **Build**: `npm run build` genera en `dist/`
- Push a `main` despliega automáticamente via GitHub Actions
- **NO editar archivos en `dist/`** — siempre trabajar en source y hacer build

### Variables de Entorno (`.env`)

```env
GEMINI_API_KEY=<api_key_para_image_gen>
```

> Nota: El `.env` no existe aún en el proyecto. Crear cuando se necesite generar imágenes.

---

## Template de Cascadas — Referencia Rápida

### Objeto `cascada` — Campos obligatorios

```javascript
const cascada = {
  // Identificación
  nombre, slug, region, zona,

  // Características físicas
  altura, caudal, dificultad, acceso, coordenadas,
  lat, lng, rio, tipoFormacion, numeroBrazos,

  // Información práctica
  mejorEpoca, entrada, horario, distanciaSantiago,

  // Contenido (TODOS obligatorios)
  descripcion,        // Texto largo
  comoLlegar,         // Texto con rutas desde Santiago + ciudad cercana
  historia,           // Historia, cultura, geología
  queHacer,           // Array de { actividad, descripcion }
  flora,              // Texto sobre flora del entorno
  fauna,              // Texto sobre fauna del entorno
  clima,              // Objeto { tipo, tempPromedio, tempVerano, tempInvierno, precipitaciones, descripcion }
  seguridad,          // Array de strings (tips)
  recomendaciones,    // Array de strings (qué llevar)
  gastronomia,        // Array de { plato, descripcion }
  alojamiento,        // Array de { nombre, tipo, precioDesde, url, descripcion }
  faq,                // Array de { pregunta, respuesta }

  // Media (ver sección "8. Imágenes reales desde Wikimedia Commons")
  imagen,             // Ruta local WebP hero: '/assets/cascadas/{slug}/hero.webp'
  imagenAlt,          // Alt text descriptivo del hero
  galeria,            // Array de { src, alt } — 4 imágenes de galería
  galeriaCreditos,    // Array de { autor, licencia, url } — atribución Wikimedia

  // Internal linking
  cascadasCercanas,      // Array de { nombre, slug, region, altura, tipo: 'cercania' } — 3 por proximidad geográfica
  cascadasRelacionadas,  // Array de { nombre, slug, region, altura, tipo: 'relacionada' } — 3 por relación semántica
};
```

### Internal Linking — Regla obligatoria

Cada página de cascada DEBE tener:

**1. Mínimo 3 enlaces inline** dentro del contenido (secciones Descripción, Historia, u otras):
- Consultar `CONTEXTO_PROYECTO.md` para identificar cascadas relacionadas, regiones y hubs
- Los enlaces deben ser **naturales y contextualmente relevantes** (no forzados)
- Usar la clase `cascada-inline-link` para estilo consistente
- Destinos típicos: página de región (`/region/{slug}`), hub de cascadas (`/cascadas`), cascadas mencionadas en el texto (`/cascadas/{slug}`)

**2. Sección "Cascadas cercanas" con 6 cards** (no 3):
- **3 por cercanía geográfica** (misma región o regiones adyacentes)
- **3 por relación semántica** (misma dificultad, tipo de experiencia, acceso similar, o relevancia temática)
- Las relaciones semánticas se definen consultando `CONTEXTO_PROYECTO.md`: gaps de contenido, co-ocurrencia de keywords, clusters por región
- Cada card lleva badges: región + tipo (Cercanía / Relacionada)

**3. Fuentes para decidir qué enlazar:**
- `CONTEXTO_PROYECTO.md` → Gaps de contenido, keywords co-ocurrentes, clusters por región
- Priorizar enlaces a páginas que existen o están planificadas en el topical map
- No enlazar a URLs que no serán creadas

### Structured Data obligatorio por página

1. **TouristAttraction** — con geo coordinates reales
2. **FAQPage** — con las preguntas del array `faq`
3. **BreadcrumbList** — Inicio > Cascadas > {Región} > {Nombre}

### Design System

| Token | Valor | Uso |
|-------|-------|-----|
| Navy | `#091d2b` | Secciones oscuras (Hero, Galería, Actividades, Clima, Seguridad, Alojamiento, Cercanas) |
| Cream | `#f4efe6` | Secciones claras (Ficha, Descripción, Flora/Fauna, Historia, Gastronomía, FAQ) |
| Cyan | `#00e5d4` | Acentos, badges, números destacados, hover states |
| Teal | `#00b4a0` | Labels secundarios |
| Archivo Black | Display | H1, H2, card titles, stats |
| DM Sans 300/400/500 | Body | Párrafos, labels, metadata |

### SEO on-page por página

- **Title**: `{nombre} — Guía completa, cómo llegar y qué hacer | Cascadas de Chile`
- **H1**: `{nombre}`
- **H2s**: Semánticamente ricos ("Cómo llegar al {nombre}", "Qué hacer en el {nombre}", etc.)
- **Meta description**: Incluir altura, región y CTA
- **Alt text** en imágenes de galería

---

## Reglas Generales

### Antes de Crear Contenido
1. Verificar en `CONTEXTO_PROYECTO.md` que el tema está DENTRO del scope (topical borders)
2. **SIEMPRE investigar con `chile-waterfalls-researcher` antes de redactar datos de cascadas**
3. Analizar intención de búsqueda con `search-intent-analyzer`
4. Asegurar internal links requeridos
5. Respetar TODAS las 15 secciones del template — no omitir ninguna

### Estructura del Proyecto

```
cascadas/
├── .claude/
│   └── agents/
│       └── chile-waterfalls-researcher.md
├── .github/
│   └── workflows/          # GitHub Actions para deploy
├── dist/                    # Build output (NO editar)
├── public/
│   └── assets/             # Imágenes estáticas
├── scripts/
│   ├── image-gen/          # Generador de imágenes con Gemini
│   │   ├── generate.py
│   │   └── .image-gen-costs.csv
│   └── seo-entropy/        # Análisis de entropía SEO
│       └── analyze.py
├── src/
│   ├── layouts/
│   │   └── Layout.astro    # Layout principal (con soporte JSON-LD)
│   ├── pages/
│   │   ├── index.astro
│   │   ├── cascadas/
│   │   │   ├── index.astro
│   │   │   └── salto-del-laja.astro  # Template de referencia
│   │   ├── blog/
│   │   └── region/
│   └── styles/
│       └── global.css
├── CONTEXTO_PROYECTO.md     # Estrategia SEO y Topical Map
├── CLAUDE.md                # Este archivo
└── package.json
```

### Sitemap
- Se genera **automáticamente** en cada `npm run build`
- **No editar el sitemap manualmente** — solo hacer build después de crear/eliminar páginas

### NO Editar Directamente
- Nunca editar archivos en `dist/` — siempre trabajar en source y hacer build
- Nunca crear contenido fuera del topical border definido en `CONTEXTO_PROYECTO.md`
- Nunca inventar datos de cascadas sin pasar por `chile-waterfalls-researcher`

---

## Tabla de Referencia Rápida

| Necesidad | Herramienta |
|-----------|-------------|
| Crear página de cascada | `chile-waterfalls-researcher` → `search-intent-analyzer` → Wikimedia images → template |
| Crear artículo de blog | `search-intent-analyzer` + `chile-waterfalls-researcher` (si menciona cascadas) |
| Analizar intención de búsqueda | `search-intent-analyzer` |
| Investigar datos de cascadas | `chile-waterfalls-researcher` |
| Analizar competidores | MCP `chrome-devtools` |
| Keyword research | MCP `dfs-kwr` |
| Analizar entidades NLP | MCP `mcp-ents` |
| Curar contenido existente | `content-curation` |
| Estrategia de internal linking | `interlinking-strategy` |
| Fotos reales de cascadas | `scripts/download-wikimedia.sh` + Wikimedia Commons API |
| Generar imágenes con IA | `python scripts/image-gen/generate.py` |
| Análisis de entropía | `python scripts/seo-entropy/analyze.py` |
| Limpiar código/archivos | `code-cleanup-analyzer` |
| Datos de Search Console | MCP `mcp-sql` |
| Comportamiento de usuarios | MCP `clarity` |

---

## Referencias

- **Contexto SEO completo**: `CONTEXTO_PROYECTO.md`
- **Template de cascada (referencia)**: `src/pages/cascadas/salto-del-laja.astro`
- **Agente investigador**: `.claude/agents/chile-waterfalls-researcher.md`
- **Image gen docs**: `scripts/image-gen/README.md`
