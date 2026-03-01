# Image Gen - Generador de Imagenes con Gemini

Script CLI para generar y editar imagenes usando la API de Google Gemini.

## Setup

### 1. Obtener API Key

1. Ve a [Google AI Studio](https://aistudio.google.com/apikey)
2. Crea o copia tu API key
3. Agregala al `.env` en la raiz del proyecto:

```
GEMINI_API_KEY=tu_api_key_aqui
```

### 2. Instalar dependencias

```bash
pip install -r scripts/image-gen/requirements.txt
```

O con el entorno conda:

```bash
/opt/anaconda3/envs/env_prueba/bin/pip install -r scripts/image-gen/requirements.txt
```

## Uso

### Generar imagen

```bash
python scripts/image-gen/generate.py --prompt "Hero banner azul degradado profesional"
```

### Especificar ruta de salida

```bash
python scripts/image-gen/generate.py \
  --prompt "Infografia de SEO tecnico" \
  --output public/assets/blog/seo-tecnico/hero.webp
```

### Usar modelo pro con alta resolucion

```bash
python scripts/image-gen/generate.py \
  --prompt "Logo minimalista de growth marketing" \
  --model pro --image-size 4K --aspect-ratio 1:1
```

### Editar imagen existente

```bash
python scripts/image-gen/generate.py \
  --prompt "Cambiar el fondo a blanco" \
  --edit public/assets/blog/imagen-original.webp
```

### Modo silencioso (para scripts)

```bash
python scripts/image-gen/generate.py \
  --prompt "Background abstracto" --quiet
# Solo imprime: /ruta/absoluta/al/archivo.webp
```

## Argumentos

| Argumento | Corto | Default | Descripcion |
|-----------|-------|---------|-------------|
| `--prompt` | `-p` | requerido | Prompt de generacion |
| `--model` | `-m` | `flash` | `flash` (rapido) o `pro` (alta calidad) |
| `--output` | `-o` | auto | Ruta completa del archivo de salida |
| `--output-dir` | `-d` | `public/assets/` | Directorio de salida |
| `--filename` | `-f` | slug del prompt | Nombre del archivo sin extension |
| `--aspect-ratio` | `-a` | `16:9` | Ratio: 1:1, 16:9, 9:16, 3:2, 4:3, etc. |
| `--image-size` | `-s` | None | 1K, 2K, 4K (solo modelo pro) |
| `--edit` | `-e` | None | Ruta a imagen existente para editar |
| `--format` | | `webp` | Formato: webp, png, jpg |
| `--quiet` | `-q` | False | Solo imprime la ruta del archivo |

## Modelos

| Alias | Model ID | Notas |
|-------|----------|-------|
| `flash` | `gemini-2.5-flash-image` | Rapido, buena calidad general |
| `pro` | `gemini-3-pro-image-preview` | Soporta `--image-size` |

## Convenciones de ruta

| Tipo | Ruta | En markdown |
|------|------|-------------|
| Blog hero | `public/assets/blog/{slug}/hero.webp` | `/assets/blog/{slug}/hero.webp` |
| Blog imagen | `public/assets/blog/{slug}/nombre.webp` | `/assets/blog/{slug}/nombre.webp` |
| OG image | `public/assets/og/nombre.webp` | `/assets/og/nombre.webp` |
| General | `public/assets/nombre.webp` | `/assets/nombre.webp` |
