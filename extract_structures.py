"""Tab 3 -> raw_structures.csv"""

import re
import openpyxl
import pandas as pd

SRC = "Data_Engineer_TechnicalChallenge.xlsx"
SHEET = "6YR Structures"

FIRST_ROW, LAST_ROW = 11, 30
COST_TYPE_BY_THEME = {8: "Design", 6: "Construction w/ Materials"}

# programme, milepost col, capital col, description col, quantity col, label, uom
BLOCKS = [
    ("Bridge Tie Deck Renewal",     2, 4, None, 3,    "Bridge",  "ties"),
    ("Culvert Replacement",         5, 6, None, None, "Culvert", None),
    ("Bridge Repairs/Replacements", 7, 9, 8,    None, "Bridge",  None),
]


def fiscal_year(band):
    return "FY" + band.strip().split("-")[1][-2:]


def mileposts(*cells):
    for cell in cells:
        if cell is None:
            continue
        if isinstance(cell, (int, float)):
            return [float(cell)]
        found = re.findall(r"\d+\.\d+|\d+", str(cell))
        if found:
            return [float(x) for x in found]
    return []


def extract():
    values = openpyxl.load_workbook(SRC, data_only=True)[SHEET]
    styles = openpyxl.load_workbook(SRC)[SHEET]      # data_only drops the fills

    lookup = pd.read_csv("lookups/structure_events.csv").fillna("")
    work = {(r.program, r.description): (r.work_group, r.event_type)
            for r in lookup.itertuples()}

    rows, placeholders = [], []
    band = None

    for r in range(FIRST_ROW, LAST_ROW + 1):
        band = values.cell(r, 1).value or band       # blank on continuation rows
        fy = fiscal_year(band) if band else None

        for program, mp_col, cost_col, desc_col, qty_col, label, uom in BLOCKS:
            capital = values.cell(r, cost_col).value

            if not capital:
                # a zero is a formula with no tie count entered, which is not
                # the same as no work planned
                if capital == 0:
                    placeholders.append(f"{chr(64 + cost_col)}{r} {fy} {program}")
                continue

            description = values.cell(r, desc_col).value if desc_col else None
            description = description.strip() if description else ""

            mps = mileposts(values.cell(r, mp_col).value, description)
            work_group, event_type = work[program, description]
            cost_type = COST_TYPE_BY_THEME[styles.cell(r, cost_col).fill.fgColor.theme]
            quantity = values.cell(r, qty_col).value if qty_col else None
            share = capital / len(mps)

            for mp in mps:
                rows.append({
                    "program": program,
                    "work_group": work_group,
                    "event_type": event_type,
                    "asset_name": f"{label} MP {mp}",
                    "asset_kind": label,
                    "milepost_start": mp, "milepost_end": mp,
                    "quantity": quantity, "quantity_uom": uom if quantity else None,
                    "cost_type": cost_type,
                    "amount": share,
                    "fiscal_year": fy,
                    "description": description,
                    "allocation_method": (f"Even split across {len(mps)} mileposts"
                                          if len(mps) > 1 else "Stated"),
                    "source_ref": f"{SHEET}!{chr(64 + cost_col)}{r}",
                })

    return pd.DataFrame(rows), values, placeholders


def check(df, ws):
    out = []

    band = None
    for r in range(FIRST_ROW, LAST_ROW + 1):
        if ws.cell(r, 1).value:
            band = ws.cell(r, 1).value
            total = ws.cell(r, 10).value
            if total:
                fy = fiscal_year(band)
                mine = df.loc[df.fiscal_year == fy, "amount"].sum()
                out.append((f"{fy} ties to J", round(mine, 2) == round(total, 2)))

    out.append(("6 yr total",
                round(df.amount.sum(), 2) == round(ws["J31"].value, 2)))
    out.append(("12 assets",
                df.groupby(["asset_kind", "milepost_start"]).ngroups == 12))

    # the fill colour and the word Engineering should agree, both ways round
    engineering = df.description.str.contains("Engineering", case=False)
    out.append(("Engineering rows are Design",
                (df[engineering].cost_type == "Design").all()))

    design = df[(df.cost_type == "Design") & (df.description != "")]
    out.append(("Design rows say Engineering",
                design.description.str.contains("Engineering", case=False).all()))

    return out


if __name__ == "__main__":
    df, ws, placeholders = extract()

    for name, passed in check(df, ws):
        print(f"  {'ok  ' if passed else 'FAIL'} {name}")

    print()
    print(df.pivot_table(index="program", columns="cost_type", values="amount",
                         aggfunc="sum", margins=True).to_string())

    print("\nzero-value cells, excluded:")
    for p in placeholders:
        print(f"  {p}")

    df.to_csv("raw_structures.csv", index=False)
    print(f"\n{len(df)} rows -> raw_structures.csv")