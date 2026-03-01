# Cascadas de Chile

> El directorio más completo de cascadas, saltos y caídas de agua a lo largo de toda Chile.

**Dominio:** cascadaschile.com
**Stack:** Astro 5 + Tailwind CSS 4
**Output:** Estático (GitHub Pages)

---

## Arquitectura del sitio

```
src/
├── layouts/
│   └── Layout.astro          ← Nav + Ticker + Footer compartido (todas las páginas)
├── pages/
│   ├── index.astro            ← Homepage
│   ├── cascadas/
│   │   ├── index.astro        ← Hub: directorio de cascadas (filtro por dificultad)
│   │   └── salto-del-laja.astro  ← Template: página individual de cascada
│   ├── region/
│   │   ├── index.astro        ← Hub: Chile de norte a sur (9 regiones)
│   │   └── los-lagos.astro    ← Template: página de región
│   └── blog/
│       ├── index.astro        ← Hub: guías y datos
│       └── mejores-cascadas-chile.astro  ← Template: artículo de blog
└── styles/
    └── global.css             ← Design tokens (Tailwind 4 @theme)
```

## Design system

| Token | Valor | Uso |
|---|---|---|
| `--color-navy` | `#091d2b` | Fondo principal |
| `--color-cyan` | `#00e5d4` | Acento primario, CTAs |
| `--color-teal` | `#00b4a0` | Footer, números |
| `--color-sky` | `#b8e8e4` | Secciones secundarias |
| `--color-cream` | `#f4efe6` | Fondos claros |
| `--font-display` | Archivo Black | Headings, números grandes |
| `--font-body` | DM Sans | Cuerpo de texto |

## Páginas implementadas

| Ruta | Tipo | Estado |
|---|---|---|
| `/` | Homepage | ✅ |
| `/cascadas` | Hub directorio | ✅ |
| `/cascadas/[nombre]` | Ficha de cascada | ✅ template |
| `/region` | Hub regiones | ✅ |
| `/region/[nombre]` | Página de región | ✅ template |
| `/blog` | Hub blog | ✅ |
| `/blog/[articulo]` | Artículo | ✅ template |
| `/mapa` | Mapa interactivo | 🔜 pendiente |

## Comandos

```sh
npm run dev       # Dev server → localhost:4321
npm run build     # Build estático → ./dist/
npm run preview   # Preview del build
```

## Contexto del proyecto

Ver `CONTEXTO_PROYECTO.md` para el análisis SEO completo: keyword universe, análisis SERP, competidores, gaps de contenido y estrategia de topical authority.
