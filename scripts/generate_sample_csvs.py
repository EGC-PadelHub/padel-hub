#!/usr/bin/env python3
"""
Genera un par de CSV de ejemplo para pruebas y los coloca en
`app/modules/dataset/error_csv`:
- error_csv/unclosed_quote.csv -> comilla sin cerrar
- error_csv/latin1_encoded.csv -> archivo codificado en latin-1

Ejecuta: python3 scripts/generate_sample_csvs.py
"""
from pathlib import Path

# Place error examples under the dataset module csv_examples location
OUT_DIR = Path("app/modules/dataset/error_csv")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1) CSV con comilla sin cerrar
unclosed = """name,score
Juan,3
Maria,"4
Pedro,2
"""
with open(OUT_DIR / "unclosed_quote.csv", "w", encoding="utf-8", newline="") as f:
    f.write(unclosed)

# 2) CSV codificado en latin-1 (bytes no válidos en utf-8 si se interpretan como tal)
latin1_text = "name,city\nAlice,Sev\xe9lla\nBob,Malaga\n"
# latin-1 encode of "Sevél la" style string; we construct proper str then encode
latin1_content = "name,city\nAlice,Sevéria\nBob,Malaga\n"
# Escribimos en latin-1 para simular fichero legacy
with open(OUT_DIR / "latin1_encoded.csv", "wb") as f:
    f.write(latin1_content.encode("latin-1"))

print(f"Generados: {OUT_DIR / 'unclosed_quote.csv'} , {OUT_DIR / 'latin1_encoded.csv'}")
