#!/usr/bin/env python3
import csv, io, json, re, sys
from datetime import datetime
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SOURCE = "https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"
OUT = Path(__file__).resolve().parents[1] / "data" / "ipca-2032.json"
MATURITY = "15/08/2032"

def norm(x): return re.sub(r"\s+", " ", str(x or "").strip()).lower()

def col(fields, names):
    m = {norm(x): x for x in fields}
    for n in names:
        if norm(n) in m: return m[norm(n)]
    return None

def number(x):
    s = str(x or "").strip()
    if not s: return None
    return float(s.replace(".", "").replace(",", ".")) if "," in s else float(s)

def date(x):
    s = str(x).strip()
    for f in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try: return datetime.strptime(s, f).date().isoformat()
        except ValueError: pass
    raise ValueError(f"Unsupported date: {x!r}")

def fetch(url):
    retry = Retry(
        total=4,
        backoff_factor=5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session.get(url, timeout=(10, 120))

def main():
    r = fetch(SOURCE)
    r.raise_for_status()
    text = r.content.decode("utf-8-sig", errors="replace")
    try: dialect = csv.Sniffer().sniff(text[:10000], delimiters=";,")
    except csv.Error:
        dialect = csv.excel; dialect.delimiter = ";"
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames: raise RuntimeError("CSV has no header")

    title = col(reader.fieldnames, ["Tipo Titulo", "Tipo do Titulo", "Titulo", "Título"])
    maturity = col(reader.fieldnames, ["Data Vencimento", "Data de Vencimento", "Vencimento"])
    dt = col(reader.fieldnames, ["Data Base", "Data", "Data Referencia", "Data de Referência"])
    buy = col(reader.fieldnames, ["PU Compra", "Preço Compra", "Preco Compra", "Preço Unitário Compra", "Preco Unitario Compra"])
    sell = col(reader.fieldnames, ["PU Venda", "Preço Venda", "Preco Venda", "Preço Unitário Venda", "Preco Unitario Venda"])
    missing = [n for n,v in {"title":title,"maturity":maturity,"date":dt,"buy":buy,"sell":sell}.items() if not v]
    if missing: raise RuntimeError("Missing CSV columns: " + ", ".join(missing))

    rows, titles = [], set()
    for row in reader:
        t = row.get(title, "")
        if norm(row.get(maturity)) != norm(MATURITY): continue
        nt = norm(t)
        if "ipca" not in nt or "juros semestrais" in nt: continue
        if "ipca+" not in nt and "ipca +" not in nt and "tesouro ipca" not in nt: continue
        titles.add(t)
        price = number(row.get(buy)) or number(row.get(sell))
        if price is not None: rows.append({"date": date(row[dt]), "close": price})

    if not rows: raise RuntimeError("No zero-coupon Tesouro IPCA+ 2032 rows found")
    if len(titles) != 1: raise RuntimeError(f"Ambiguous matching titles: {sorted(titles)}")
    rows = list({x["date"]: x for x in rows}.values())
    rows.sort(key=lambda x: x["date"])
    OUT.write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("Matched:", next(iter(titles)))
    print("Rows:", len(rows), "Latest:", rows[-1])

if __name__ == "__main__":
    try: main()
    except Exception as e:
        print("ERROR:", e, file=sys.stderr); sys.exit(1)
