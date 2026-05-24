#!/usr/bin/env python3
"""
Google Search Console — Extracción mensual + insights accionables.

Saca datos de GSC (clicks, impresiones, CTR, posición) para un período mensual,
compara contra el mes anterior, e identifica oportunidades para priorizar las
próximas implementaciones (cascadas/regiones a crear, contenido a curar).

Uso:
    # Últimos 28 días completos (default), comparado con los 28 previos
    python scripts/gsc-insights/monthly.py

    # Un mes calendario específico
    python scripts/gsc-insights/monthly.py --month 2026-04

    # Rango custom
    python scripts/gsc-insights/monthly.py --start 2026-04-01 --end 2026-04-30

    # Cambiar propiedad o key
    python scripts/gsc-insights/monthly.py --site sc-domain:cascadaschile.com --key /ruta/key.json

Salida:
    - Resumen ejecutivo en consola (top pages, top queries, insights)
    - CSVs por dimensión en gsc-insights-output/{periodo}/
    - Un insights.md con las recomendaciones accionables
"""

import argparse
import calendar
import csv
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
DEFAULT_KEY = Path(__file__).resolve().parent.parent / "google-indexing" / "facundogrowth.json"
DEFAULT_SITE = "sc-domain:cascadaschile.com"
ROW_LIMIT = 25000
# GSC tiene ~2-3 días de delay. No pedir datos más recientes que esto.
DATA_LAG_DAYS = 3


# ─────────────────────────────────────────────────────────────────────────────
# Auth + query
# ─────────────────────────────────────────────────────────────────────────────
def get_service(key_path):
    creds = service_account.Credentials.from_service_account_file(str(key_path), scopes=SCOPES)
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def query(service, site, start, end, dimensions, row_limit=ROW_LIMIT, filters=None):
    """Pagina la Search Analytics API y devuelve todas las filas."""
    rows = []
    start_row = 0
    while True:
        body = {
            "startDate": start,
            "endDate": end,
            "dimensions": dimensions,
            "rowLimit": row_limit,
            "startRow": start_row,
            "dataState": "final",
        }
        if filters:
            body["dimensionFilterGroups"] = [{"filters": filters}]
        resp = service.searchanalytics().query(siteUrl=site, body=body).execute()
        batch = resp.get("rows", [])
        rows.extend(batch)
        if len(batch) < row_limit:
            break
        start_row += row_limit
    return rows


def rows_to_records(rows, dimensions):
    """Convierte las filas crudas de la API en dicts planos."""
    out = []
    for r in rows:
        rec = {}
        for i, dim in enumerate(dimensions):
            rec[dim] = r["keys"][i]
        rec["clicks"] = r.get("clicks", 0)
        rec["impressions"] = r.get("impressions", 0)
        rec["ctr"] = r.get("ctr", 0)
        rec["position"] = r.get("position", 0)
        out.append(rec)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Períodos
# ─────────────────────────────────────────────────────────────────────────────
def resolve_periods(args):
    """Devuelve (cur_start, cur_end, prev_start, prev_end, label)."""
    if args.start and args.end:
        cs = datetime.strptime(args.start, "%Y-%m-%d").date()
        ce = datetime.strptime(args.end, "%Y-%m-%d").date()
        label = f"{cs}_a_{ce}"
    elif args.month:
        y, m = map(int, args.month.split("-"))
        cs = date(y, m, 1)
        ce = date(y, m, calendar.monthrange(y, m)[1])
        label = args.month
    else:
        # Últimos 28 días completos terminando hace DATA_LAG_DAYS
        ce = date.today() - timedelta(days=DATA_LAG_DAYS)
        cs = ce - timedelta(days=27)
        label = f"ultimos28d_{ce}"

    span = (ce - cs).days + 1
    pe = cs - timedelta(days=1)
    ps = pe - timedelta(days=span - 1)
    return cs.isoformat(), ce.isoformat(), ps.isoformat(), pe.isoformat(), label


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de formato
# ─────────────────────────────────────────────────────────────────────────────
def pct(n, d):
    return (n / d * 100) if d else 0.0


def delta_str(cur, prev):
    if prev == 0:
        return "nuevo" if cur > 0 else "—"
    d = (cur - prev) / prev * 100
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.0f}%"


def short_url(url, site):
    """Acorta la URL al path para legibilidad."""
    domain = site.replace("sc-domain:", "")
    u = url.replace("https://", "").replace("http://", "")
    if u.startswith(domain):
        path = u[len(domain):]
        return path if path else "/"
    return u


def write_csv(path, records, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for rec in records:
            w.writerow({k: rec.get(k, "") for k in fieldnames})


# ─────────────────────────────────────────────────────────────────────────────
# Insights
# ─────────────────────────────────────────────────────────────────────────────
def build_insights(site, pages_cur, pages_prev, queries_cur, queries_prev):
    """Genera bloques de insight accionables a partir de los records."""
    prev_pages = {p["page"]: p for p in pages_prev}
    prev_queries = {q["query"]: q for q in queries_prev}

    # 1. Top pages por clicks
    top_pages = sorted(pages_cur, key=lambda p: p["clicks"], reverse=True)[:20]

    # 2. Top queries por clicks
    top_queries = sorted(queries_cur, key=lambda q: q["clicks"], reverse=True)[:20]

    # 3. Striking distance: queries en posición 5-20 con impresiones reales.
    #    Subir estas a top-3 es la palanca de clicks más rápida.
    striking = sorted(
        [q for q in queries_cur if 5 <= q["position"] <= 20 and q["impressions"] >= 50],
        key=lambda q: q["impressions"], reverse=True,
    )[:25]

    # 4. Alto impressions + bajo CTR: demanda existente mal capturada (title/meta o intent gap)
    if queries_cur:
        imp_median = sorted([q["impressions"] for q in queries_cur])[len(queries_cur) // 2]
    else:
        imp_median = 0
    low_ctr = sorted(
        [q for q in queries_cur
         if q["impressions"] >= max(100, imp_median) and q["ctr"] < 0.02 and q["position"] <= 20],
        key=lambda q: q["impressions"], reverse=True,
    )[:20]

    # 5. Páginas que más crecen / caen (MoM)
    movers = []
    for p in pages_cur:
        prev = prev_pages.get(p["page"], {})
        movers.append({
            "page": p["page"],
            "clicks": p["clicks"],
            "prev_clicks": prev.get("clicks", 0),
            "diff": p["clicks"] - prev.get("clicks", 0),
        })
    risers = sorted([m for m in movers if m["diff"] > 0], key=lambda m: m["diff"], reverse=True)[:10]
    fallers = sorted([m for m in movers if m["diff"] < 0], key=lambda m: m["diff"])[:10]

    # 6. Demanda de contenido: queries de cascadas/regiones SIN página dedicada todavía.
    #    Heurística: query con buen volumen de impresiones que rankea flojo (pos > 10),
    #    señal de que falta una página específica para esa cascada/región.
    content_gaps = sorted(
        [q for q in queries_cur if q["impressions"] >= 100 and q["position"] > 10],
        key=lambda q: q["impressions"], reverse=True,
    )[:25]

    # 7. Canonicalización: misma página indexada en >1 variante (http/https, con/sin
    #    trailing slash). Cada variante divide impresiones y equity. Quick win SEO.
    groups = {}
    for p in pages_cur:
        u = p["page"].split("://", 1)[-1].rstrip("/")  # normaliza protocolo + slash final
        groups.setdefault(u, []).append(p)
    canon_dupes = []
    for norm, variants in groups.items():
        if len(variants) > 1:
            canon_dupes.append({
                "normalized": norm,
                "variants": sorted(variants, key=lambda v: v["impressions"], reverse=True),
                "total_impressions": sum(v["impressions"] for v in variants),
                "total_clicks": sum(v["clicks"] for v in variants),
            })
    canon_dupes.sort(key=lambda d: d["total_impressions"], reverse=True)

    return {
        "top_pages": top_pages,
        "top_queries": top_queries,
        "striking": striking,
        "low_ctr": low_ctr,
        "risers": risers,
        "fallers": fallers,
        "content_gaps": content_gaps,
        "canon_dupes": canon_dupes,
        "prev_pages": prev_pages,
        "prev_queries": prev_queries,
    }


def print_report(site, period_label, cur, prev, totals_cur, totals_prev, ins):
    line = "═" * 70
    print(f"\n{line}")
    print(f"  GSC INSIGHTS · {site}")
    print(f"  Período: {cur[0]} → {cur[1]}   (vs {prev[0]} → {prev[1]})")
    print(line)

    tc, tp = totals_cur, totals_prev
    print("\n📊 TOTALES")
    print(f"  Clicks:      {tc['clicks']:>8,}   ({delta_str(tc['clicks'], tp['clicks'])} MoM)")
    print(f"  Impresiones: {tc['impressions']:>8,}   ({delta_str(tc['impressions'], tp['impressions'])} MoM)")
    print(f"  CTR:         {pct(tc['clicks'], tc['impressions']):>7.2f}%")
    print(f"  Posición:    {tc['position']:>7.1f}")

    print("\n🏆 TOP PÁGINAS POR CLICKS")
    print(f"  {'#':>2}  {'clicks':>7}  {'MoM':>6}  {'impr':>8}  {'CTR':>6}  {'pos':>5}  página")
    for i, p in enumerate(ins["top_pages"], 1):
        prev_c = ins["prev_pages"].get(p["page"], {}).get("clicks", 0)
        print(f"  {i:>2}  {p['clicks']:>7,}  {delta_str(p['clicks'], prev_c):>6}  "
              f"{p['impressions']:>8,}  {p['ctr']*100:>5.1f}%  {p['position']:>5.1f}  "
              f"{short_url(p['page'], site)}")

    print("\n🔎 TOP QUERIES POR CLICKS")
    print(f"  {'#':>2}  {'clicks':>7}  {'impr':>8}  {'CTR':>6}  {'pos':>5}  query")
    for i, q in enumerate(ins["top_queries"][:15], 1):
        print(f"  {i:>2}  {q['clicks']:>7,}  {q['impressions']:>8,}  "
              f"{q['ctr']*100:>5.1f}%  {q['position']:>5.1f}  {q['query']}")

    print("\n🎯 STRIKING DISTANCE (pos 5–20, subir a top-3 = clicks rápidos)")
    print(f"  {'impr':>8}  {'pos':>5}  {'CTR':>6}  query")
    for q in ins["striking"][:15]:
        print(f"  {q['impressions']:>8,}  {q['position']:>5.1f}  {q['ctr']*100:>5.1f}%  {q['query']}")

    print("\n⚠️  ALTO IMPRESIONES + BAJO CTR (revisar title/meta o intent)")
    print(f"  {'impr':>8}  {'pos':>5}  {'CTR':>6}  query")
    for q in ins["low_ctr"][:12]:
        print(f"  {q['impressions']:>8,}  {q['position']:>5.1f}  {q['ctr']*100:>5.1f}%  {q['query']}")

    print("\n🧩 GAPS DE CONTENIDO (demanda con ranking débil → ¿crear página?)")
    print(f"  {'impr':>8}  {'pos':>5}  query")
    for q in ins["content_gaps"][:15]:
        print(f"  {q['impressions']:>8,}  {q['position']:>5.1f}  {q['query']}")

    if ins["canon_dupes"]:
        print("\n🔁 CANONICALIZACIÓN (misma URL en varias variantes → equity dividido)")
        for d in ins["canon_dupes"][:12]:
            print(f"  {d['total_impressions']:>6,} impr totales  →  /{d['normalized'].split('/',1)[-1]}")
            for v in d["variants"]:
                proto = v["page"].split("://", 1)[0]
                slash = "/" if v["page"].rstrip().endswith("/") else "(sin slash)"
                print(f"        {v['impressions']:>5,} impr  {proto}  {slash}")

    print("\n📈 PÁGINAS QUE MÁS CRECEN (MoM)")
    for m in ins["risers"][:8]:
        print(f"  +{m['diff']:>5,}  ({m['prev_clicks']}→{m['clicks']})  {short_url(m['page'], site)}")

    print("\n📉 PÁGINAS QUE MÁS CAEN (MoM)")
    for m in ins["fallers"][:8]:
        print(f"  {m['diff']:>6,}  ({m['prev_clicks']}→{m['clicks']})  {short_url(m['page'], site)}")

    print(f"\n{line}\n")


def write_insights_md(out_dir, site, period_label, cur, prev, totals_cur, totals_prev, ins):
    md = []
    md.append(f"# GSC Insights — {site}\n")
    md.append(f"**Período:** {cur[0]} → {cur[1]} (vs {prev[0]} → {prev[1]})  ")
    md.append(f"**Generado:** {datetime.now():%Y-%m-%d %H:%M}\n")

    tc, tp = totals_cur, totals_prev
    md.append("## Totales\n")
    md.append("| Métrica | Actual | MoM |")
    md.append("|---|--:|--:|")
    md.append(f"| Clicks | {tc['clicks']:,} | {delta_str(tc['clicks'], tp['clicks'])} |")
    md.append(f"| Impresiones | {tc['impressions']:,} | {delta_str(tc['impressions'], tp['impressions'])} |")
    md.append(f"| CTR | {pct(tc['clicks'], tc['impressions']):.2f}% | — |")
    md.append(f"| Posición media | {tc['position']:.1f} | — |\n")

    md.append("## Top páginas por clicks\n")
    md.append("| # | Página | Clicks | MoM | Impr | CTR | Pos |")
    md.append("|--:|---|--:|--:|--:|--:|--:|")
    for i, p in enumerate(ins["top_pages"], 1):
        prev_c = ins["prev_pages"].get(p["page"], {}).get("clicks", 0)
        md.append(f"| {i} | {short_url(p['page'], site)} | {p['clicks']:,} | "
                  f"{delta_str(p['clicks'], prev_c)} | {p['impressions']:,} | "
                  f"{p['ctr']*100:.1f}% | {p['position']:.1f} |")

    md.append("\n## Striking distance (pos 5–20)\n")
    md.append("Subir estas queries a top-3 es la palanca de clicks más rápida.\n")
    md.append("| Query | Impr | Pos | CTR |")
    md.append("|---|--:|--:|--:|")
    for q in ins["striking"]:
        md.append(f"| {q['query']} | {q['impressions']:,} | {q['position']:.1f} | {q['ctr']*100:.1f}% |")

    md.append("\n## Alto impresiones + bajo CTR\n")
    md.append("Demanda existente mal capturada — revisar title/meta description o intent.\n")
    md.append("| Query | Impr | Pos | CTR |")
    md.append("|---|--:|--:|--:|")
    for q in ins["low_ctr"]:
        md.append(f"| {q['query']} | {q['impressions']:,} | {q['position']:.1f} | {q['ctr']*100:.1f}% |")

    md.append("\n## Gaps de contenido (¿crear página?)\n")
    md.append("Queries con demanda real pero ranking débil (pos > 10). Candidatas a página propia.\n")
    md.append("| Query | Impr | Pos |")
    md.append("|---|--:|--:|")
    for q in ins["content_gaps"]:
        md.append(f"| {q['query']} | {q['impressions']:,} | {q['position']:.1f} |")

    if ins["canon_dupes"]:
        md.append("\n## Canonicalización (URLs duplicadas)\n")
        md.append("Misma página indexada en varias variantes (http/https, con/sin slash). "
                  "Cada variante divide impresiones y equity — forzar 301 a una sola canónica.\n")
        md.append("| URL normalizada | Impr totales | Variantes |")
        md.append("|---|--:|---|")
        for d in ins["canon_dupes"]:
            vs = " · ".join(
                f"{v['page'].split('://',1)[0]}{'/'if v['page'].rstrip().endswith('/') else '∅'}={v['impressions']}"
                for v in d["variants"])
            md.append(f"| /{d['normalized'].split('/',1)[-1]} | {d['total_impressions']:,} | {vs} |")

    md.append("\n## Páginas que más crecen (MoM)\n")
    md.append("| Página | Δ clicks | Antes → Ahora |")
    md.append("|---|--:|---|")
    for m in ins["risers"]:
        md.append(f"| {short_url(m['page'], site)} | +{m['diff']:,} | {m['prev_clicks']} → {m['clicks']} |")

    md.append("\n## Páginas que más caen (MoM)\n")
    md.append("| Página | Δ clicks | Antes → Ahora |")
    md.append("|---|--:|---|")
    for m in ins["fallers"]:
        md.append(f"| {short_url(m['page'], site)} | {m['diff']:,} | {m['prev_clicks']} → {m['clicks']} |")

    (out_dir / "insights.md").write_text("\n".join(md), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="GSC extracción mensual + insights")
    ap.add_argument("--site", default=DEFAULT_SITE, help="Propiedad GSC (ej: sc-domain:cascadaschile.com)")
    ap.add_argument("--key", default=str(DEFAULT_KEY), help="Ruta al JSON de la service account")
    ap.add_argument("--month", help="Mes calendario YYYY-MM (ej: 2026-04)")
    ap.add_argument("--start", help="Fecha inicio YYYY-MM-DD (usar con --end)")
    ap.add_argument("--end", help="Fecha fin YYYY-MM-DD (usar con --start)")
    ap.add_argument("--outdir", default="gsc-insights-output", help="Carpeta de salida")
    args = ap.parse_args()

    key_path = Path(args.key)
    if not key_path.exists():
        print(f"Error: no se encontró la key en '{key_path}'", file=sys.stderr)
        sys.exit(1)

    cs, ce, ps, pe, label = resolve_periods(args)
    cur, prev = (cs, ce), (ps, pe)

    print(f"Conectando a {args.site} ...")
    svc = get_service(key_path)

    # Extracción dimensión por dimensión, período actual y previo
    print(f"Extrayendo período actual ({cs} → {ce}) ...")
    pages_cur = rows_to_records(query(svc, args.site, cs, ce, ["page"]), ["page"])
    queries_cur = rows_to_records(query(svc, args.site, cs, ce, ["query"]), ["query"])
    pq_cur = rows_to_records(query(svc, args.site, cs, ce, ["page", "query"]), ["page", "query"])
    country_cur = rows_to_records(query(svc, args.site, cs, ce, ["country"]), ["country"])
    device_cur = rows_to_records(query(svc, args.site, cs, ce, ["device"]), ["device"])

    print(f"Extrayendo período previo ({ps} → {pe}) ...")
    pages_prev = rows_to_records(query(svc, args.site, ps, pe, ["page"]), ["page"])
    queries_prev = rows_to_records(query(svc, args.site, ps, pe, ["query"]), ["query"])

    # Totales
    def totals(recs):
        c = sum(r["clicks"] for r in recs)
        i = sum(r["impressions"] for r in recs)
        # posición media ponderada por impresiones
        pos = sum(r["position"] * r["impressions"] for r in recs) / i if i else 0
        return {"clicks": c, "impressions": i, "position": pos}

    totals_cur = totals(pages_cur)
    totals_prev = totals(pages_prev)

    ins = build_insights(args.site, pages_cur, pages_prev, queries_cur, queries_prev)

    # Salida a disco
    out_dir = Path(args.outdir) / label
    out_dir.mkdir(parents=True, exist_ok=True)
    metric_cols = ["clicks", "impressions", "ctr", "position"]
    write_csv(out_dir / "pages.csv", sorted(pages_cur, key=lambda x: x["clicks"], reverse=True),
              ["page"] + metric_cols)
    write_csv(out_dir / "queries.csv", sorted(queries_cur, key=lambda x: x["clicks"], reverse=True),
              ["query"] + metric_cols)
    write_csv(out_dir / "page_query.csv", sorted(pq_cur, key=lambda x: x["clicks"], reverse=True),
              ["page", "query"] + metric_cols)
    write_csv(out_dir / "country.csv", sorted(country_cur, key=lambda x: x["clicks"], reverse=True),
              ["country"] + metric_cols)
    write_csv(out_dir / "device.csv", sorted(device_cur, key=lambda x: x["clicks"], reverse=True),
              ["device"] + metric_cols)
    write_insights_md(out_dir, args.site, label, cur, prev, totals_cur, totals_prev, ins)

    # Reporte en consola
    print_report(args.site, label, cur, prev, totals_cur, totals_prev, ins)
    print(f"✔ CSVs e insights.md guardados en: {out_dir}/\n")


if __name__ == "__main__":
    main()
