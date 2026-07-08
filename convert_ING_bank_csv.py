#!/usr/bin/env python3
"""
Convert a Dutch bank CSV export to the format expected by better-personal-finance.

Input columns (semicolon-delimited, quoted):
  "Datum","Naam / Omschrijving","Rekening","Tegenrekening","Code",
  "Af Bij","Bedrag (EUR)","Mutatiesoort","Mededelingen"

Output columns:
  date, amount_in, amount_out, payee, notes,
  Rekening, Tegenrekening, Code, Mutatiesoort

Transformations applied:
  - Datum           -> date        (DD-MM-YYYY -> YYYY-MM-DD)
  - Naam/Omschr.    -> payee
  - Bedrag (EUR)    -> amount_in   when Af Bij == "Bij"  (money received)
                    -> amount_out  when Af Bij == "Af"   (money sent)
                    Numbers converted from Dutch format (1.234,56) to 1234.56
  - Mededelingen    -> notes
  - Rekening, Tegenrekening, Code, Mutatiesoort  passed through unchanged

Usage:
  python convert_bank_csv.py <input.csv>
  python convert_bank_csv.py <input.csv> <output.csv>   # explicit output path
"""

import csv
import sys
from datetime import datetime
from pathlib import Path


# The bank sometimes uses semicolons as the delimiter (ING) and sometimes
# commas. This function detects which one is used.
def _detect_delimiter(sample: str) -> str:
    if sample.count(";") >= sample.count(","):
        return ";"
    return ","


def _parse_amount(value: str) -> str:
    """Convert Dutch-formatted number (1.234,56) to plain decimal (1234.56)."""
    return value.replace(".", "").replace(",", ".")


def _convert_date(value: str) -> str:
    """Convert DD-MM-YYYY to YYYY-MM-DD."""
    return datetime.strptime(value.strip(), "%d-%m-%Y").strftime("%Y-%m-%d")


def convert(input_path: Path, output_path: Path) -> None:
    raw = input_path.read_text(encoding="utf-8-sig")
    delimiter = _detect_delimiter(raw.splitlines()[0] if raw else ",")

    rows: list[dict[str, str]] = []
    missing_cols: list[str] = []

    with input_path.open(newline="", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile, delimiter=delimiter)

        required = {"Datum", "Naam / Omschrijving", "Af Bij", "Bedrag (EUR)", "Mededelingen",
                    "Rekening", "Tegenrekening", "Code", "Mutatiesoort"}
        first_row = True

        for row in reader:
            if first_row:
                first_row = False
                missing_cols = [c for c in required if c not in row]
                if missing_cols:
                    print(
                        f"Error: the following expected columns were not found in the CSV:\n"
                        f"  {missing_cols}\n"
                        f"Detected columns: {list(row.keys())}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

            af_bij = row["Af Bij"].strip()
            raw_amount = _parse_amount(row["Bedrag (EUR)"].strip())

            if af_bij not in ("Af", "Bij"):
                print(
                    f"Warning: row {reader.line_num} has unexpected 'Af Bij' value "
                    f"'{af_bij}' — skipping row.",
                    file=sys.stderr,
                )
                continue

            rows.append({
                "date":          _convert_date(row["Datum"]),
                "amount_in":     raw_amount if af_bij == "Bij" else "",
                "amount_out":    raw_amount if af_bij == "Af"  else "",
                "payee":         row["Naam / Omschrijving"].strip(),
                "notes":         row["Mededelingen"].strip(),
                "Rekening":      row["Rekening"].strip(),
                "Tegenrekening": row["Tegenrekening"].strip(),
                "Code":          row["Code"].strip(),
                "Mutatiesoort":  row["Mutatiesoort"].strip(),
            })

    fieldnames = [
        "date", "amount_in", "amount_out", "payee", "notes",
        "Rekening", "Tegenrekening", "Code", "Mutatiesoort",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Converted {len(rows)} row(s)  ->  {output_path}")
    print()
    print("Import tip: in the app use these column mappings:")
    print("  Date        -> date")
    print("  Amount In   -> amount_in")
    print("  Amount Out  -> amount_out")
    print("  Payee       -> payee")
    print("  Notes       -> notes")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        print("Usage: python convert_bank_csv.py <input.csv> [output.csv]", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else \
        input_path.with_stem(input_path.stem + "_converted")

    convert(input_path, output_path)


if __name__ == "__main__":
    main()
