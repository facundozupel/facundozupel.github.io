#!/usr/bin/env python3
"""
Analisis de Entropia SEO (Shannon) para terminos de competidores.

Identifica terminos obligatorios (consenso) vs diferenciadores (especialistas)
midiendo la distribucion estadistica de terminos across competidores usando
entropia de Shannon.

Uso CLI:
    python analyze.py --input competitors.json --output results.json --top 20
    python analyze.py --input competitors.json --quiet

Uso como modulo:
    from analyze import run_analysis
    results = run_analysis(input_data)
"""

import argparse
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from statistics import mean, median, stdev

# --- Constantes ---

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STOPWORDS_FILE = Path(__file__).resolve().parent / "stopwords_es.txt"

# Clasificacion de entropia (normalizada 0-1)
CONSENSUS_THRESHOLD = 0.3       # H_norm < 0.3 = consenso
SPECIALIST_THRESHOLD = 0.7      # H_norm > 0.7 = especialista
DOC_FREQ_MIN_RATIO = 0.6        # Consenso requiere >= 60% de docs
NOISE_MIN_DOCS = 2              # Aparece en < 2 docs = ruido

# Ponderacion de headers
HEADER_WEIGHT_MULTIPLIER = 1.5  # Terminos en H1-H3 suben en ranking

MIN_TERM_LENGTH = 3             # Filtrar tokens de menos de 3 caracteres
MIN_COMPETITORS = 2             # Minimo de competidores para analisis


# --- Utilidades ---


def log(msg: str, quiet: bool = False) -> None:
    """Imprime un mensaje con prefijo visual."""
    if not quiet:
        print(f"  {msg}")


def log_step(step: str, quiet: bool = False) -> None:
    """Imprime un encabezado de paso."""
    if not quiet:
        print(f"\n--- {step}")


def log_kv(key: str, value: str, quiet: bool = False) -> None:
    """Imprime un par clave-valor alineado."""
    if not quiet:
        print(f"  {key:<24} {value}")


# --- Procesamiento de Texto ---


def load_stopwords(lang: str = "spanish") -> set:
    """Carga stopwords. Intenta nltk primero, fallback a archivo local."""
    try:
        import nltk
        try:
            from nltk.corpus import stopwords as nltk_stopwords
            return set(nltk_stopwords.words(lang))
        except LookupError:
            nltk.download("stopwords", quiet=True)
            from nltk.corpus import stopwords as nltk_stopwords
            return set(nltk_stopwords.words(lang))
    except (ImportError, Exception):
        pass

    # Fallback a archivo local
    if STOPWORDS_FILE.exists():
        text = STOPWORDS_FILE.read_text(encoding="utf-8")
        return {w.strip().lower() for w in text.splitlines() if w.strip()}

    return set()


def tokenize(text: str, stopwords: set) -> list:
    """Limpia y tokeniza texto para analisis de entropia."""
    # Normalizar unicode (acentos etc)
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    # Quitar puntuacion y numeros sueltos
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\b\d+\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = text.split()
    # Filtrar stopwords y tokens cortos
    return [t for t in tokens if t not in stopwords and len(t) >= MIN_TERM_LENGTH]


def extract_header_terms(headers: list, stopwords: set) -> set:
    """Extrae terminos unicos de headers (H1, H2, H3)."""
    terms = set()
    for header in headers:
        # Parsear formato "H1: texto", "H2: texto"
        match = re.match(r"^H[1-3]:\s*(.+)$", header, re.IGNORECASE)
        text = match.group(1) if match else header
        tokens = tokenize(text, stopwords)
        terms.update(tokens)
    return terms


# --- Calculos de Entropia ---


def calculate_tf(tokens: list) -> dict:
    """Calcula Term Frequency normalizada para un documento."""
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = len(tokens)
    return {term: count / total for term, count in counts.items()}


def calculate_shannon_entropy(tf_matrix: dict) -> dict:
    """
    Calcula entropia de Shannon para cada termino across documentos.

    H(t) = -Sum_d( p(t,d) * log2(p(t,d)) )
    donde p(t,d) = TF(t,d) / Sum_D(TF(t,d))

    Returns: {term: entropy_value}
    """
    # Recopilar todos los terminos
    all_terms = set()
    for tf in tf_matrix.values():
        all_terms.update(tf.keys())

    entropy = {}
    for term in all_terms:
        # Obtener TF del termino en cada documento
        tf_values = []
        for doc_id, tf in tf_matrix.items():
            if term in tf:
                tf_values.append(tf[term])

        # Calcular distribucion de probabilidad
        total_tf = sum(tf_values)
        if total_tf == 0:
            continue

        h = 0.0
        for tf_val in tf_values:
            p = tf_val / total_tf
            if p > 0:
                h -= p * math.log2(p)

        entropy[term] = h

    return entropy


def calculate_doc_frequency(tf_matrix: dict) -> dict:
    """Cuenta en cuantos documentos aparece cada termino."""
    doc_freq = Counter()
    for tf in tf_matrix.values():
        for term in tf:
            doc_freq[term] += 1
    return dict(doc_freq)


# --- Clasificacion ---


def classify_terms(entropy: dict, doc_freq: dict, tf_matrix: dict,
                   header_terms: set, num_docs: int, urls: list) -> dict:
    """
    Clasifica terminos en consensus, specialist, o noise.

    - Consensus: H_norm < 0.3 AND doc_freq >= 60% de docs
    - Specialist: H_norm > 0.7 AND doc_freq >= 2 pero < 60%
    - Noise: doc_freq < 2
    """
    max_entropy = math.log2(num_docs) if num_docs > 1 else 1.0
    min_docs_consensus = max(2, math.ceil(num_docs * DOC_FREQ_MIN_RATIO))

    consensus = []
    specialist = []

    for term, h in entropy.items():
        h_norm = h / max_entropy if max_entropy > 0 else 0
        df = doc_freq.get(term, 0)
        in_headers = term in header_terms

        # Calcular TF promedio
        tf_values = [tf.get(term, 0) for tf in tf_matrix.values()]
        avg_tf = mean(tf_values) if tf_values else 0

        entry = {
            "term": term,
            "entropy": round(h, 4),
            "entropy_normalized": round(h_norm, 4),
            "doc_frequency": df,
            "avg_tf": round(avg_tf, 6),
            "in_headers": in_headers,
        }

        # Clasificar
        if df < NOISE_MIN_DOCS:
            continue  # Noise - descartar

        if h_norm < CONSENSUS_THRESHOLD and df >= min_docs_consensus:
            consensus.append(entry)
        elif h_norm > SPECIALIST_THRESHOLD and df >= NOISE_MIN_DOCS:
            # Agregar source_urls para especialistas
            source_urls = []
            for i, (doc_id, tf) in enumerate(tf_matrix.items()):
                if term in tf and tf[term] > 0:
                    if i < len(urls):
                        source_urls.append(urls[i])
            entry["source_urls"] = source_urls
            specialist.append(entry)

    # Ordenar: headers primero (x1.5 peso), luego por avg_tf descendente
    def sort_key(item):
        weight = HEADER_WEIGHT_MULTIPLIER if item["in_headers"] else 1.0
        return -(item["avg_tf"] * weight)

    consensus.sort(key=sort_key)
    specialist.sort(key=sort_key)

    return {"consensus": consensus, "specialist": specialist}


# --- I/O ---


def load_input(path: str) -> dict:
    """Carga y valida JSON de entrada."""
    p = Path(path)
    if not p.exists():
        print(f"ERROR: Archivo no encontrado: {path}")
        sys.exit(1)

    data = json.loads(p.read_text(encoding="utf-8"))

    # Validacion basica
    if "competitors" not in data:
        print("ERROR: JSON debe tener campo 'competitors'")
        sys.exit(1)

    if len(data["competitors"]) < MIN_COMPETITORS:
        print(f"ERROR: Se requieren al menos {MIN_COMPETITORS} competidores")
        sys.exit(1)

    for i, comp in enumerate(data["competitors"]):
        if "body_text" not in comp:
            print(f"ERROR: Competidor {i} sin campo 'body_text'")
            sys.exit(1)

    return data


def build_output(keyword: str, num_docs: int, entropy: dict,
                 classified: dict, top_n: int) -> dict:
    """Arma JSON de salida con estadisticas y terminos clasificados."""
    values = list(entropy.values())

    stats = {}
    if values:
        stats = {
            "mean": round(mean(values), 4),
            "median": round(median(values), 4),
            "std": round(stdev(values), 4) if len(values) > 1 else 0,
            "min": round(min(values), 4),
            "max": round(max(values), 4),
        }

    return {
        "keyword": keyword,
        "document_count": num_docs,
        "term_count": len(entropy),
        "entropy_stats": stats,
        "consensus_terms": classified["consensus"][:top_n],
        "specialist_terms": classified["specialist"][:top_n],
    }


def render_histogram(values: list, bins: int = 10, width: int = 40,
                     quiet: bool = False) -> str:
    """Genera histograma ASCII de la distribucion de entropia."""
    if not values or quiet:
        return ""

    min_val = min(values)
    max_val = max(values)
    if min_val == max_val:
        return f"  Todos los valores = {min_val:.2f}"

    bin_width = (max_val - min_val) / bins
    counts = [0] * bins

    for v in values:
        idx = min(int((v - min_val) / bin_width), bins - 1)
        counts[idx] += 1

    max_count = max(counts)
    lines = []

    for i in range(bins):
        lo = min_val + i * bin_width
        hi = lo + bin_width
        bar_len = int((counts[i] / max_count) * width) if max_count > 0 else 0
        bar = "#" * bar_len
        lines.append(f"  {lo:5.2f}-{hi:5.2f} | {bar} ({counts[i]})")

    return "\n".join(lines)


# --- Entry Points ---


def run_analysis(input_data: dict, top_n: int = 20,
                 lang: str = "spanish", quiet: bool = False) -> dict:
    """
    Ejecuta analisis de entropia completo. Importable como modulo.

    Args:
        input_data: Dict con 'keyword' y 'competitors'
        top_n: Cantidad de terminos top por categoria
        lang: Idioma para stopwords
        quiet: Suprimir output a consola

    Returns:
        Dict con resultados del analisis
    """
    keyword = input_data.get("keyword", "sin keyword")
    competitors = input_data["competitors"]
    num_docs = len(competitors)

    log_step(f"Analisis de Entropia SEO: '{keyword}'", quiet)
    log_kv("Competidores", str(num_docs), quiet)

    # Cargar stopwords
    log_step("Cargando stopwords", quiet)
    stopwords = load_stopwords(lang)
    log_kv("Stopwords cargadas", str(len(stopwords)), quiet)

    # Tokenizar cada documento
    log_step("Tokenizando documentos", quiet)
    tf_matrix = {}
    all_header_terms = set()
    urls = []

    for i, comp in enumerate(competitors):
        url = comp.get("url", f"doc_{i}")
        urls.append(url)
        headers = comp.get("headers", [])

        # Extraer terminos de headers
        h_terms = extract_header_terms(headers, stopwords)
        all_header_terms.update(h_terms)

        # Tokenizar body
        tokens = tokenize(comp["body_text"], stopwords)

        # Agregar terminos de headers al tokenizado (peso extra)
        header_tokens = []
        for h in headers:
            match = re.match(r"^H[1-3]:\s*(.+)$", h, re.IGNORECASE)
            text = match.group(1) if match else h
            header_tokens.extend(tokenize(text, stopwords))
        tokens.extend(header_tokens)  # Headers cuentan doble

        tf_matrix[url] = calculate_tf(tokens)
        log_kv(f"  Doc {i+1}", f"{len(tokens)} tokens - {url[:60]}", quiet)

    # Calcular entropia
    log_step("Calculando entropia de Shannon", quiet)
    entropy = calculate_shannon_entropy(tf_matrix)
    doc_freq = calculate_doc_frequency(tf_matrix)
    log_kv("Terminos unicos", str(len(entropy)), quiet)

    # Clasificar
    log_step("Clasificando terminos", quiet)
    classified = classify_terms(
        entropy, doc_freq, tf_matrix, all_header_terms, num_docs, urls
    )
    log_kv("Consenso", str(len(classified["consensus"])), quiet)
    log_kv("Especialistas", str(len(classified["specialist"])), quiet)

    # Histograma
    if not quiet and entropy:
        log_step("Distribucion de Entropia", quiet)
        hist = render_histogram(list(entropy.values()))
        print(hist)

    # Construir output
    output = build_output(keyword, num_docs, entropy, classified, top_n)

    # Mostrar top terminos
    if not quiet:
        log_step(f"Top {min(top_n, len(classified['consensus']))} Terminos de Consenso (OBLIGATORIOS)", quiet)
        for t in classified["consensus"][:top_n]:
            marker = " [H]" if t["in_headers"] else ""
            log(f"{t['term']:<25} H={t['entropy_normalized']:.2f}  docs={t['doc_frequency']}/{num_docs}  TF={t['avg_tf']:.4f}{marker}", quiet)

        log_step(f"Top {min(top_n, len(classified['specialist']))} Terminos Especialistas (DIFERENCIACION)", quiet)
        for t in classified["specialist"][:top_n]:
            marker = " [H]" if t["in_headers"] else ""
            log(f"{t['term']:<25} H={t['entropy_normalized']:.2f}  docs={t['doc_frequency']}/{num_docs}  TF={t['avg_tf']:.4f}{marker}", quiet)

    return output


def main():
    """Entry point CLI."""
    parser = argparse.ArgumentParser(
        description="Analisis de Entropia SEO (Shannon) - Identifica terminos obligatorios vs diferenciadores"
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Ruta al JSON de entrada con datos de competidores"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Ruta para guardar JSON de resultados (opcional, imprime a stdout si no se especifica)"
    )
    parser.add_argument(
        "--top", "-t", type=int, default=20,
        help="Cantidad de terminos top por categoria (default: 20)"
    )
    parser.add_argument(
        "--lang", "-l", default="spanish",
        help="Idioma para stopwords (default: spanish)"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Solo output JSON, sin logs"
    )

    args = parser.parse_args()

    # Cargar input
    input_data = load_input(args.input)

    # Ejecutar analisis
    results = run_analysis(input_data, top_n=args.top, lang=args.lang, quiet=args.quiet)

    # Output
    if args.output:
        out_path = Path(args.output)
        out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        if not args.quiet:
            log_step("Resultados guardados", args.quiet)
            log(f"Archivo: {out_path}", args.quiet)
    elif args.quiet:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
