#!/usr/bin/env python3
"""Describe the LAYOUT of Excel files without printing any cell contents.

For each sheet it prints:
  - size and number of merged-cell ranges
  - a masked picture of the first rows, so the title rows and header row can be
    located:   T12 = text of 12 characters   N = number   D = date/time
               B = true/false                .  = empty
  - a per-column profile over the whole sheet (how full, what types)

No names, scores or other values are printed. Sheet names and file names are.

Setup:  pip install openpyxl xlrd        (xlrd is only needed for old .xls files)
Run:    python3 inspect_excel.py docs
        python3 inspect_excel.py docs --rows 20      # show more top rows
"""
import argparse
import datetime as dt
from pathlib import Path

EXTS = {".xlsx", ".xlsm", ".xls"}


def mask(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return "."
    if isinstance(v, bool):
        return "B"
    if isinstance(v, (int, float)):
        return "N"
    if isinstance(v, (dt.datetime, dt.date, dt.time)):
        return "D"
    return f"T{len(str(v).strip())}"


def col_letter(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def load_sheets(path):
    """Yield (sheet_name, rows, merged_count). Format is detected from the file's
    first bytes, so a wrongly named file (e.g. 'x.xls.xls') still opens."""
    with open(path, "rb") as f:
        magic = f.read(8)
    if magic[:2] == b"PK":                                   # xlsx / xlsm
        from openpyxl import load_workbook
        with open(path, "rb") as f:
            wb = load_workbook(f, data_only=True)
            for ws in wb.worksheets:
                rows = [list(r) for r in ws.iter_rows(values_only=True)]
                yield ws.title, rows, len(ws.merged_cells.ranges)
    elif magic[:4] == b"\xd0\xcf\x11\xe0":                   # legacy .xls
        import xlrd
        wb = xlrd.open_workbook(path, formatting_info=False)
        for sh in wb.sheets():
            rows = []
            for r in range(sh.nrows):
                row = []
                for c in range(sh.ncols):
                    cell = sh.cell(r, c)
                    if cell.ctype == xlrd.XL_CELL_DATE:
                        row.append(dt.datetime(1900, 1, 1))  # placeholder: only the type matters
                    elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                        row.append(bool(cell.value))
                    elif cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                        row.append(None)
                    else:
                        row.append(cell.value)
                rows.append(row)
            yield sh.name, rows, len(getattr(sh, "merged_cells", []))
    else:
        raise ValueError("not an Excel file (unrecognised file signature)")


def describe(path, top):
    print(f"\n{'=' * 78}\nFILE: {path}")
    for name, rows, merged in load_sheets(path):
        while rows and all(mask(c) == "." for c in rows[-1]):          # trim empty tail
            rows.pop()
        ncols = max((max((i + 1 for i, c in enumerate(r) if mask(c) != "."), default=0) for r in rows), default=0)
        print(f"\n  SHEET: {name!r}   rows: {len(rows)}   columns: {ncols}   merged ranges: {merged}")
        if not rows or not ncols:
            print("    (empty)")
            continue
        rows = [(r + [None] * ncols)[:ncols] for r in rows]

        shown = min(ncols, 30)
        print("    Top rows, masked" + (f" (first {shown} of {ncols} columns)" if shown < ncols else "") + ":")
        print("      row | " + " ".join(f"{col_letter(i):>4}" for i in range(shown)))
        for ri, r in enumerate(rows[:top], 1):
            print(f"      {ri:>3} | " + " ".join(f"{mask(c):>4}" for c in r[:shown]))

        print("    Column profile (all rows):")
        for ci in range(ncols):
            kinds = {}
            lengths = []
            for r in rows:
                m = mask(r[ci])
                if m == ".":
                    continue
                k = "text" if m[0] == "T" else {"N": "number", "D": "date", "B": "bool"}[m]
                kinds[k] = kinds.get(k, 0) + 1
                if k == "text":
                    lengths.append(int(m[1:]))
            if not kinds:
                continue
            filled = sum(kinds.values())
            desc = ", ".join(f"{k} x{n}" for k, n in sorted(kinds.items(), key=lambda kv: -kv[1]))
            extra = f"; text length {min(lengths)}-{max(lengths)}" if lengths else ""
            print(f"      {col_letter(ci):>3}: {100 * filled // len(rows):>3}% filled  [{desc}{extra}]")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="an Excel file or a folder to scan")
    ap.add_argument("--rows", type=int, default=12, help="how many top rows to show masked (default 12)")
    a = ap.parse_args()
    target = Path(a.target)
    files = [target] if target.is_file() else sorted(
        p for p in target.rglob("*") if p.suffix.lower() in EXTS and not p.name.startswith("~$"))
    if not files:
        raise SystemExit(f"No Excel files found under {target}")
    for f in files:
        try:
            describe(f, a.rows)
        except ImportError as e:
            print(f"\nFILE: {f}\n  needs an extra package: pip install {e.name}")
        except Exception as e:                                   # keep going on a broken file
            print(f"\nFILE: {f}\n  could not read: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()