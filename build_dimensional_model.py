"""Three raw extracts -> dimensional model in model_dim/"""

from pathlib import Path
import pandas as pd

OUT = Path("model_dim")

BRANCH, DIVISION, SUBDIVISION = "Westport", "Central", "Hanover"
LOCATION_SOURCE = "Assignment brief - not in the source workbook"

FIRST_FY, LAST_FY = 2026, 2032
BUILD_COSTS = ("CNST", "CWM")

ASSET_CLASSES = [
    ("TRK", "Track"),
    ("STR", "Structures"),
    ("CNS", "Communications & Signals"),
]

ASSET_TYPES = [
    ("CP",   "Control Point",         "CNS", "Dispatcher-controlled signal and switch location"),
    ("AUTO", "Automatic Signal",      "CNS", "Intermediate signal driven by track circuit occupancy"),
    ("XING", "Grade Crossing Signal", "CNS", "Highway-rail crossing warning equipment"),
    ("CURV", "Curve",                 "TRK", "Curved track subject to accelerated rail wear"),
    ("TO",   "Turnout",               "TRK", "Switch assembly on or between mainlines"),
    ("TOI",  "Industry Turnout",      "TRK", "Switch assembly serving an industry track or lead"),
    ("TSEG", "Track Segment",         "TRK", "Linear run under the timber and surfacing programme"),
    ("STA",  "Station Track",         "TRK", "Track within a station area"),
    ("BRDG", "Bridge",                "STR", "Structure carrying track over a gap"),
    ("CULV", "Culvert",               "STR", "Drainage structure through an embankment"),
]

# the brief asks for replacement, rehabilitation or upgrade. the specific job
# lives in dim_work_group
EVENT_TYPES = [
    ("REPL", "Replacement",    "Asset or complete component set replaced with new"),
    ("REHB", "Rehabilitation", "Asset restored toward original condition"),
    ("UPGR", "Upgrade",        "Asset modified to a higher specification"),
]

WORK_GROUPS = [
    ("Signal Upgrade Phase 1",   "Comms and Signals"),
    ("Signal Upgrade Phase 2",   "Comms and Signals"),
    ("Signal Upgrade Phase 3",   "Comms and Signals"),
    ("Curve Rail Replacement",   "TS Program Est"),
    ("Turnout Replacement",      "TS Program Est"),
    ("Timber & Surfacing",       "TS Program Est"),
    ("Stations Tie Replacement", "TS Program Est"),
    ("Culvert Replacement",      "6YR Structures"),
    ("Tie Deck Renewal",         "6YR Structures"),
    ("Retaining Structures",     "6YR Structures"),
    ("Concrete Encasement",      "6YR Structures"),
    ("Steel Repairs",            "6YR Structures"),
    ("Span Replacement",         "6YR Structures"),
]

COST_TYPES = [
    ("DSGN", "Design",                    "Engineering and design only",             1, 0, 0),
    ("MATL", "Material",                  "Materials only",                          0, 1, 0),
    ("CNST", "Construction",              "Construction labour, materials separate", 0, 0, 1),
    ("CWM",  "Construction w/ Materials", "Construction and materials combined",     0, 1, 1),
]

TS_EVENT_TYPE = {
    "Curve Rail Replacement":   "REPL",
    "Turnout Replacement":      "REPL",
    "Stations Tie Replacement": "REPL",
    "Timber & Surfacing":       "REHB",
}

ASSET_KIND_CODE = {name: code for code, name, _, _ in ASSET_TYPES}
EVENT_TYPE_CODE = {name: code for code, name, _ in EVENT_TYPES}
COST_TYPE_CODE = {name: code for code, name, *_ in COST_TYPES}


def fy_key(fiscal_year):
    return int(str(fiscal_year).lstrip("FY"))


def to_fiscal_year(calendar_year, quarter):
    # Q3 and Q4 are Jul-Dec, so they fall in the next fiscal year
    year = calendar_year + 1 if quarter in ("Q3", "Q4") else calendar_year
    return f"FY{year % 100}"


def calendar_key(year, quarter):
    return year * 10 + int(quarter[1])


def allocation_of(note):
    note = str(note)
    if note.startswith("Unattributed"):
        return "UNATTRIBUTED", 0
    if note.startswith("Even split"):
        return "EVEN_SPLIT", 0
    if note.startswith("Unit rate"):
        return "UNIT_RATE", 1
    return "STATED", 1


def signal_type(name):
    if "Control Point" in name:
        return "CP"
    if name.startswith("Auto"):
        return "AUTO"
    if "Crossing" in name:
        return "XING"
    raise ValueError(f"can't classify signal asset: {name}")


def load_comms():
    df = pd.read_csv("raw_comms_signals.csv")
    return pd.DataFrame({
        "asset_bk": "CNS|" + df.location_name,
        "asset_name": df.location_name,
        "asset_type_code": df.location_name.map(signal_type),
        "milepost_start": df.milepost,
        "milepost_end": df.milepost,
        "track": None,
        "quantity": 1.0,
        "quantity_uom": "unit",
        "work_group": "Signal Upgrade Phase " + df.phase.astype(str),
        "event_type_code": "UPGR",
        "cost_type_code": df.cost_type.map(COST_TYPE_CODE),
        "amount_usd": df.estimated_cost,
        "fiscal_year": [to_fiscal_year(y, q)
                        for y, q in zip(df.calendar_year, df.quarter)],
        "calendar_year": df.calendar_year,
        "quarter": df.quarter,
        "allocation_note": "Stated",
        "source_ref": df.source_ref,
    })


def load_track():
    df = pd.read_csv("raw_ts_program.csv")
    return pd.DataFrame({
        "asset_bk": "TRK|" + df.asset_name,
        "asset_name": df.asset_name,
        "asset_type_code": df.asset_kind.map(ASSET_KIND_CODE),
        "milepost_start": df.milepost_start,
        "milepost_end": df.milepost_end,
        "track": df.track,
        "quantity": df.quantity,
        "quantity_uom": df.quantity_uom,
        "work_group": df.program,
        "event_type_code": df.program.map(TS_EVENT_TYPE),
        "cost_type_code": df.cost_type.map(COST_TYPE_CODE),
        "amount_usd": df.amount,
        "fiscal_year": df.fiscal_year,
        "calendar_year": pd.NA,          # this tab gives a fiscal year only
        "quarter": pd.NA,
        "allocation_note": df.allocation_method,
        "source_ref": df.source_ref,
    })


def load_structures():
    df = pd.read_csv("raw_structures.csv")
    return pd.DataFrame({
        "asset_bk": "STR|" + df.asset_name,
        "asset_name": df.asset_name,
        "asset_type_code": df.asset_kind.map(ASSET_KIND_CODE),
        "milepost_start": df.milepost_start,
        "milepost_end": df.milepost_end,
        "track": None,
        "quantity": df.quantity,
        "quantity_uom": df.quantity_uom,
        "work_group": df.work_group,
        "event_type_code": df.event_type.map(EVENT_TYPE_CODE),
        "cost_type_code": df.cost_type.map(COST_TYPE_CODE),
        "amount_usd": df.amount,
        "fiscal_year": df.fiscal_year,
        "calendar_year": pd.NA,
        "quarter": pd.NA,
        "allocation_note": df.allocation_method,
        "source_ref": df.source_ref,
    })


def numbered(df, key):
    df.insert(0, key, range(1, len(df) + 1))
    return df


def build_asset_class():
    return numbered(pd.DataFrame(ASSET_CLASSES,
                                 columns=["asset_class_code", "asset_class_name"]),
                    "asset_class_key")


def build_asset_type(classes):
    df = pd.DataFrame(ASSET_TYPES, columns=["asset_type_code", "asset_type_name",
                                            "asset_class_code",
                                            "asset_type_description"])
    df = df.merge(classes, on="asset_class_code").drop(columns="asset_class_name")
    return numbered(df, "asset_type_key")


def build_event_type():
    return numbered(pd.DataFrame(EVENT_TYPES,
                                 columns=["event_type_code", "event_type_name",
                                          "event_type_description"]),
                    "event_type_key")


def build_work_group():
    return numbered(pd.DataFrame(WORK_GROUPS,
                                 columns=["work_group_name", "source_tab"]),
                    "work_group_key")


def build_cost_type():
    return numbered(pd.DataFrame(COST_TYPES,
                                 columns=["cost_type_code", "cost_type_name",
                                          "cost_scope", "includes_design",
                                          "includes_material",
                                          "includes_construction"]),
                    "cost_type_key")


def build_fiscal_period():
    # no unknown member: every row states or implies a fiscal year, and the
    # fact build raises if one fails to resolve
    return pd.DataFrame([{
        "fiscal_period_key": year % 100,
        "fiscal_year": f"FY{year % 100}",
        "fy_start": f"{year - 1}-07-01",
        "fy_end": f"{year}-06-30",
    } for year in range(FIRST_FY, LAST_FY + 1)])


def build_calendar_period(long):
    # only the quarters the source actually states
    stated = long.dropna(subset=["quarter"])[["calendar_year", "quarter"]]
    rows = [{
        "calendar_period_key": calendar_key(int(y), q),
        "calendar_year": int(y),
        "calendar_quarter": q,
        "period_label": f"{int(y)} {q}",
    } for y, q in sorted(set(map(tuple, stated.values)))]
    return pd.DataFrame(rows)


def build_asset(long, types):
    df = (long.groupby("asset_bk", as_index=False)
              .agg(asset_name=("asset_name", "first"),
                   asset_type_code=("asset_type_code", "first"),
                   milepost_start=("milepost_start", "first"),
                   milepost_end=("milepost_end", "first"),
                   track=("track", "first"),
                   quantity=("quantity", "first"),
                   quantity_uom=("quantity_uom", "first"),
                   source_ref=("source_ref", "first")))

    df = df.merge(types[["asset_type_key", "asset_type_code"]],
                  on="asset_type_code", validate="many_to_one")

    # the same three values on all 53 assets, so not worth a dimension
    df["branch"], df["division"] = BRANCH, DIVISION
    df["subdivision"], df["location_source"] = SUBDIVISION, LOCATION_SOURCE

    df = df.sort_values(["asset_type_code", "milepost_start", "asset_name"],
                        na_position="last").reset_index(drop=True)
    df = numbered(df, "asset_key")

    prefix = df.asset_bk.str[:3]
    df["asset_id"] = prefix + "-" + (df.groupby(prefix).cumcount() + 1).map("{:03d}".format)

    return df[["asset_key", "asset_id", "asset_name", "asset_type_key",
               "milepost_start", "milepost_end", "track", "quantity",
               "quantity_uom", "branch", "division", "subdivision",
               "location_source", "source_ref", "asset_bk"]]


def build_event(long, assets, event_types, work_groups):
    long = long.merge(assets[["asset_key", "asset_bk"]], on="asset_bk")
    long["event_bk"] = long.asset_key.astype(str) + "|" + long.work_group
    long["fiscal_period_key"] = long.fiscal_year.map(fy_key)

    # an event happens in the year its construction happens. design comes
    # before and material is bought ahead of it, so neither dates the event.
    # reading it off the fiscal period key rather than recomputing from a
    # calendar year is what stops this drifting out of step with the fact.
    build = long[long.cost_type_code.isin(BUILD_COSTS)]
    planned = build.groupby("event_bk").fiscal_period_key.min()

    df = (long.groupby("event_bk", as_index=False)
              .agg(asset_key=("asset_key", "first"),
                   event_type_code=("event_type_code", "first"),
                   work_group=("work_group", "first")))
    df["planned_fiscal_period_key"] = df.event_bk.map(planned)

    if df.planned_fiscal_period_key.isna().any():
        missing = df.loc[df.planned_fiscal_period_key.isna(), "event_bk"].tolist()
        raise ValueError(f"event with no construction cost: {missing}")
    df["planned_fiscal_period_key"] = df.planned_fiscal_period_key.astype(int)

    df = df.merge(event_types[["event_type_key", "event_type_code"]],
                  on="event_type_code", validate="many_to_one")
    df = df.merge(work_groups[["work_group_key", "work_group_name"]],
                  left_on="work_group", right_on="work_group_name",
                  validate="many_to_one")

    df = df.sort_values(["asset_key", "work_group"]).reset_index(drop=True)
    df = numbered(df, "event_key")
    df["event_id"] = "EV-" + (df.index + 1).map("{:03d}".format)

    return df[["event_key", "event_id", "asset_key", "event_type_key",
               "work_group_key", "planned_fiscal_period_key", "event_bk"]], long


def build_fact(long, events, cost_types, fiscal, calendar):
    df = long.merge(events[["event_key", "event_bk"]], on="event_bk")
    df = df.merge(cost_types[["cost_type_key", "cost_type_code"]],
                  on="cost_type_code", validate="many_to_one")

    unknown = set(df.fiscal_period_key) - set(fiscal.fiscal_period_key)
    if unknown:
        raise ValueError(f"fiscal period outside the dimension: {unknown}")

    # null, not a placeholder row, where the source gives no quarter
    df["calendar_period_key"] = [
        calendar_key(int(y), q) if pd.notna(q) else pd.NA
        for y, q in zip(df.calendar_year, df.quarter)
    ]
    df["calendar_period_key"] = df.calendar_period_key.astype("Int64")

    unknown = set(df.calendar_period_key.dropna()) - set(calendar.calendar_period_key)
    if unknown:
        raise ValueError(f"calendar period outside the dimension: {unknown}")

    allocation = df.allocation_note.map(allocation_of)
    df["allocation_code"] = [code for code, _ in allocation]
    df["is_source_traceable"] = [flag for _, flag in allocation]

    df = df.sort_values(["event_key", "cost_type_key"]).reset_index(drop=True)
    df = numbered(df, "cost_key")

    return df[["cost_key", "event_key", "cost_type_key", "fiscal_period_key",
               "calendar_period_key", "amount_usd", "allocation_code",
               "is_source_traceable", "allocation_note", "source_ref"]]


def run_checks(fact, dims):
    asset, event = dims["dim_asset"], dims["dim_event"]
    types, classes = dims["dim_asset_type"], dims["dim_asset_class"]
    fiscal, calendar = dims["dim_fiscal_period"], dims["dim_calendar_period"]

    out = []

    for label, child, key, parent in [
        ("fact -> event",       fact,  "event_key",        event),
        ("fact -> cost type",   fact,  "cost_type_key",    dims["dim_cost_type"]),
        ("fact -> fiscal",      fact,  "fiscal_period_key", fiscal),
        ("event -> asset",      event, "asset_key",        asset),
        ("event -> event type", event, "event_type_key",   dims["dim_event_type"]),
        ("event -> work group", event, "work_group_key",   dims["dim_work_group"]),
        ("asset -> asset type", asset, "asset_type_key",   types),
        ("asset type -> class", types, "asset_class_key",  classes),
    ]:
        out.append((label, child[key].isin(parent[key]).all()))

    out.append(("event -> fiscal",
                event.planned_fiscal_period_key.isin(fiscal.fiscal_period_key).all()))
    out.append(("fact -> calendar (optional)",
                fact.calendar_period_key.dropna()
                    .isin(calendar.calendar_period_key).all()))

    for name, table in dims.items():
        out.append((f"{name} key unique", table.iloc[:, 0].is_unique))
    out.append(("cost_key unique", fact.cost_key.is_unique))

    # nothing orphaned the other way either
    out.append(("every asset has an event",
                asset.asset_key.isin(event.asset_key).all()))
    out.append(("every event has a cost",
                event.event_key.isin(fact.event_key).all()))
    out.append(("no unused work group",
                dims["dim_work_group"].work_group_key.isin(event.work_group_key).all()))
    out.append(("no unused fiscal period",
                fiscal.fiscal_period_key.isin(fact.fiscal_period_key).all()))
    out.append(("no unused calendar period",
                calendar.calendar_period_key.isin(
                    fact.calendar_period_key.dropna()).all()))

    out.append(("fact grain unique", not fact.duplicated(
        ["event_key", "cost_type_key", "fiscal_period_key"]).any()))

    out.append(("no money in a dimension", not any(
        "amount" in c or "usd" in c for t in dims.values() for c in t.columns)))

    # an event and its own construction cost must agree on the year
    build = (fact.merge(dims["dim_cost_type"][["cost_type_key", "cost_type_code"]],
                        on="cost_type_key")
                 .query("cost_type_code in @BUILD_COSTS")
                 .merge(event[["event_key", "planned_fiscal_period_key"]],
                        on="event_key"))
    out.append(("event year == construction year",
                (build.fiscal_period_key == build.planned_fiscal_period_key).all()))

    totals = (fact.merge(event[["event_key", "asset_key"]], on="event_key")
                  .merge(asset[["asset_key", "asset_type_key"]], on="asset_key")
                  .merge(types[["asset_type_key", "asset_class_key"]], on="asset_type_key")
                  .merge(classes, on="asset_class_key")
                  .groupby("asset_class_name").amount_usd.sum())

    for name, expected in [("Communications & Signals", 11_229_000),
                           ("Track", 12_487_000),
                           ("Structures", 12_147_330.32)]:
        out.append((f"{name} total", round(totals[name], 2) == expected))

    out.append(("grand total", round(fact.amount_usd.sum(), 2) == 35_863_330.32))

    return out


def write_gis_export(fact, dims):
    asset, types, classes = (dims["dim_asset"], dims["dim_asset_type"],
                             dims["dim_asset_class"])
    event, event_types = dims["dim_event"], dims["dim_event_type"]
    fiscal = dims["dim_fiscal_period"]

    cost = (fact.merge(event[["event_key", "asset_key"]], on="event_key")
                .groupby("asset_key").amount_usd.sum().rename("total_cost"))

    # two bridges carry two events each, so take the earliest for the label
    per_asset = (event.merge(event_types[["event_type_key", "event_type_name"]],
                             on="event_type_key")
                      .merge(fiscal[["fiscal_period_key", "fiscal_year"]],
                             left_on="planned_fiscal_period_key",
                             right_on="fiscal_period_key")
                      .sort_values(["asset_key", "planned_fiscal_period_key"])
                      .groupby("asset_key")
                      .agg(planned_fiscal_year=("fiscal_year", "first"),
                           event_type_name=("event_type_name", "first"),
                           n_events=("event_key", "size")))

    df = (asset.merge(types[["asset_type_key", "asset_type_name", "asset_class_key"]],
                      on="asset_type_key")
               .merge(classes, on="asset_class_key")
               .merge(cost, on="asset_key")
               .merge(per_asset, on="asset_key"))

    df["location_type"] = (df.milepost_start != df.milepost_end).map(
        {True: "Linear", False: "Point"})

    unplaceable = df[df.milepost_start.isna()]
    df = df[df.milepost_start.notna()].sort_values("milepost_start")

    df = df[["asset_id", "asset_name", "asset_type_name", "asset_class_name",
             "milepost_start", "milepost_end", "location_type", "track",
             "total_cost", "planned_fiscal_year", "event_type_name", "n_events"]]
    df.to_csv(OUT / "gis_assets.csv", index=False)

    print(f"\n{len(df)} locatable assets -> gis_assets.csv  "
          f"(${df.total_cost.sum():,.2f})")
    for _, row in unplaceable.iterrows():
        print(f"  excluded: {row.asset_id} {row.asset_name} "
              f"${row.total_cost:,.0f} - no milepost in the source")


def main():
    OUT.mkdir(exist_ok=True)

    long = pd.concat([load_comms(), load_track(), load_structures()],
                     ignore_index=True)

    classes = build_asset_class()
    types = build_asset_type(classes)
    event_types = build_event_type()
    work_groups = build_work_group()
    cost_types = build_cost_type()
    fiscal = build_fiscal_period()
    calendar = build_calendar_period(long)

    assets = build_asset(long, types)
    events, long = build_event(long, assets, event_types, work_groups)
    fact = build_fact(long, events, cost_types, fiscal, calendar)

    dims = {"dim_asset_class": classes, "dim_asset_type": types,
            "dim_asset": assets, "dim_event_type": event_types,
            "dim_work_group": work_groups, "dim_event": events,
            "dim_cost_type": cost_types, "dim_fiscal_period": fiscal,
            "dim_calendar_period": calendar}

    failures = 0
    for name, passed in run_checks(fact, dims):
        failures += not passed
        print(f"  {'ok  ' if passed else 'FAIL'} {name}")
    print(f"\n  {failures} failure(s)")

    print(f"\n  {'fact_cost':<22}{len(fact):>5}")
    for name, table in dims.items():
        print(f"  {name:<22}{len(table):>5}")

    # the business keys were only there for joining
    dims["dim_asset"] = assets.drop(columns="asset_bk")
    dims["dim_event"] = events.drop(columns="event_bk")

    wide = (fact.merge(dims["dim_event"][["event_key", "asset_key"]], on="event_key")
                .merge(dims["dim_asset"][["asset_key", "asset_type_key"]], on="asset_key")
                .merge(types[["asset_type_key", "asset_class_key"]], on="asset_type_key")
                .merge(classes, on="asset_class_key")
                .merge(cost_types[["cost_type_key", "cost_type_name"]], on="cost_type_key")
                .merge(fiscal[["fiscal_period_key", "fiscal_year"]], on="fiscal_period_key"))

    print("\ninventory")
    print(dims["dim_asset"].merge(types, on="asset_type_key")
                           .merge(classes, on="asset_class_key")
                           .groupby(["asset_class_name", "asset_type_name"])
                           .size().to_string())

    print("\ncost by class and type")
    print(wide.pivot_table(index="asset_class_name", columns="cost_type_name",
                           values="amount_usd", aggfunc="sum",
                           margins=True).to_string())

    print("\nspend by fiscal year")
    print(wide.pivot_table(index="fiscal_year", columns="asset_class_name",
                           values="amount_usd", aggfunc="sum", fill_value=0,
                           margins=True).to_string())

    print("\nhow each figure was derived")
    print(fact.groupby("allocation_code")
              .agg(rows=("cost_key", "size"), usd=("amount_usd", "sum")).to_string())

    tables = {"fact_cost": fact, **dims}
    for name, table in tables.items():
        table.to_csv(OUT / f"{name}.csv", index=False)
    with pd.ExcelWriter(OUT / "asset_inventory_dimensional.xlsx") as writer:
        for name, table in tables.items():
            table.to_excel(writer, sheet_name=name.upper()[:31], index=False)

    print(f"\n{len(tables)} tables -> {OUT}/")
    write_gis_export(fact, dims)


if __name__ == "__main__":
    main()