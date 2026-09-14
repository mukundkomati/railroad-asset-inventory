# Railroad Asset Inventory

Data model and GIS visualisation for a railroad capital programme covering
track, structures, and comms & signal equipment. Built from the supplied
workbook and mapped onto the FRA rail network at Westport Branch / Central
Division / Hanover Subdivision.

53 assets, 55 lifecycle events, 103 cost records, $35,863,330.32.

## Running it

Needs pandas, openpyxl, geopandas, shapely.

```bash
python extract_comms_signals.py
python extract_ts_program.py
python extract_structures.py
python build_dimensional_model.py
python place_assets.py
```

First three read the workbook, one per tab, and write a flat CSV each. Fourth
builds the model into `model_dim/`. Fifth places the assets on the line and
writes `asset_inventory.gpkg`.

Every script checks itself as it goes. 66 checks in total, 32 of them on the
model build alone. All passing.

## Layout

```
*.py                  the pipeline, in the order above
lookups/              turnout, station and structure-event lists that had to
                      be read by hand rather than parsed
raw_*.csv             one row per asset per cost type, still at source grain
model_dim/            1 fact table, 9 dimensions, plus an xlsx of all ten
*.gpkg                the rail line, the FRA mileposts, the placed assets
vpra_map.qgz          QGIS project
*.png                 exported maps
```

## The model

Kimball, snowflaked on asset class. Grain is one row per event, per cost type,
per period.

```
fact_cost
  -> dim_cost_type
  -> dim_fiscal_period          always set
  -> dim_calendar_period        null where there is no quarter
  -> dim_event
       -> dim_event_type
       -> dim_work_group
       -> dim_fiscal_period     planned year
       -> dim_asset
            -> dim_asset_type
                 -> dim_asset_class
```

Two period dimensions because the tabs disagree on grain. Comms & Signals gives
a calendar quarter, the other two give a fiscal year only. Fiscal year is the
one they share so it is on every row; the calendar key is null on the 49 rows
that have no quarter.

Every cost row keeps a `source_ref` back to the cell it came from and an
`allocation_code` saying how it was arrived at.

## Assumptions

**$80,000 in I8 has no owner.** The eleven turnouts are covered by J8 and K8.
This is left over with no location and no description. Carried as an "Unknown
Turnout" with no milepost so Track still ties to $12,487,000. Not mapped.

**CP Ford's four turnouts are FY29, the rest FY28.** K8 is the rate times four
and CP Ford is the only quantity-four row. FY28 and FY29 both reconcile
separately, not just the total.

**T&S does M1 first.** The matrix splits $7,000,000 across FY30 and FY31 but
never says which mainline goes first. Reverse it and $3.5M moves years.

**Even splits where nothing better exists.** Five culverts share a design
figure, five stations share a lump sum with no unit rate anywhere on the sheet.
Both split evenly and flagged `is_source_traceable = 0`. $4,477,000 in total.

**Bridges at MP 16.9 and 28.8 are one asset each.** Each appears under both tie
deck renewals and repairs. One bridge, two events. That is why Structures is 12
assets and 14 events.

**Westport / Central / Hanover come from the brief, not the workbook.** Stamped
on all 53 assets with `location_source` saying where they came from.

Also worth knowing: the $600,000 in I24 is not a cost, it marks which turnouts
are Industry turnouts (600,000 / 150,000 = 4, and there are four industry rows).
And cost type on the structures tab only exists as cell fill colour, which I
cross-checked against the word "Engineering" in the description.

## Checks

Totals tie to the workbook to the cent, year by year rather than just on the
grand total.

| | |
|---|---|
| Comms & Signals | $11,229,000.00 |
| Track | $12,487,000.00 |
| Structures | $12,147,330.32 |

The model build also checks foreign keys both directions, fact grain, that no
dimension holds money, and that every event agrees with its own construction
cost on the fiscal year.

## Mapping

The FRA line layer returns 93 segments for this subdivision and they do not
join into one chain. They merge into five pieces. The longest is 55 miles and
carries none of the mileposts we need; the right one is 50 miles and carries
all 25 of MP 9 to 33. Picked by counting mileposts within 50 m of each piece,
not by length.

Each asset is then placed between the two nearest FRA milepost points.

Sanity check: the T&S segments run MP 15.0 to 32.5, so 17.5 miles by
definition. Measured along the placed geometry they come out at 17.59. FRA's
mileposts are not exactly a mile apart, so that gap builds up over seventeen
brackets.

FRA calls its milepost positions approximate. Per the brief, the line is not
the real one, so nothing here will match satellite imagery.