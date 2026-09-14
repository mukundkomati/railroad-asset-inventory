"""model_dim/gis_assets.csv -> asset_inventory.gpkg"""

import geopandas as gpd
import pandas as pd
from shapely.ops import linemerge, substring

METRES = 5070                 # NAD83 / Conus Albers
SNAP = 50                     # how close a milepost has to be to count
FIRST_MP, LAST_MP = 9, 33     # the range the assets occupy
MILE = 1609.344


def flatten(geometries):
    # the GeoPackage stores these as MultiLineStrings, linemerge wants plain ones
    parts = []
    for g in geometries:
        if g is None:
            continue
        parts.extend(g.geoms if g.geom_type == "MultiLineString" else [g])
    return parts


def pick_route(line, mileposts):
    merged = linemerge(flatten(line.geometry))
    pieces = ([merged] if merged.geom_type == "LineString"
              else sorted(merged.geoms, key=lambda g: g.length, reverse=True))

    wanted = mileposts[mileposts.MILEPOST.between(FIRST_MP, LAST_MP)]

    # the longest piece is a different run of track entirely, so pick on which
    # one carries the mileposts rather than on length
    best, best_hits = None, -1
    for i, piece in enumerate(pieces):
        hits = (wanted.geometry.apply(piece.distance) < SNAP).sum()
        print(f"  piece {i}: {piece.length / MILE:6.2f} mi, "
              f"{hits}/{len(wanted)} of MP {FIRST_MP}-{LAST_MP}")
        if hits > best_hits:
            best, best_hits = piece, hits

    if best_hits < len(wanted):
        raise SystemExit(f"no single piece carries MP {FIRST_MP}-{LAST_MP} "
                         f"(best {best_hits}/{len(wanted)}) - the route breaks "
                         f"inside the range the assets occupy")
    return best


def anchors(mileposts, route):
    on_route = mileposts[mileposts.geometry.apply(route.distance) < SNAP].copy()
    on_route["along_m"] = on_route.geometry.apply(route.project)
    on_route = on_route.sort_values("MILEPOST").reset_index(drop=True)

    # if distance does not move one way as the milepost climbs, the route is wrong
    steps = on_route.along_m.diff().dropna()
    if not ((steps > 0).all() or (steps < 0).all()):
        print("  WARNING: milepost distances are not monotonic")

    return on_route


def locate(milepost, anchor_table):
    below = anchor_table[anchor_table.MILEPOST <= milepost].tail(1)
    above = anchor_table[anchor_table.MILEPOST >= milepost].head(1)

    if below.empty:
        below, above = anchor_table.iloc[[0]], anchor_table.iloc[[1]]
    if above.empty:
        below, above = anchor_table.iloc[[-2]], anchor_table.iloc[[-1]]

    lo_mp, lo_d = below.MILEPOST.iloc[0], below.along_m.iloc[0]
    hi_mp, hi_d = above.MILEPOST.iloc[0], above.along_m.iloc[0]

    if lo_mp == hi_mp:
        return lo_d
    return lo_d + (milepost - lo_mp) / (hi_mp - lo_mp) * (hi_d - lo_d)


def main():
    line = gpd.read_file("hanover_line.gpkg").to_crs(METRES)
    mileposts = gpd.read_file("hanover_mileposts.gpkg").to_crs(METRES)
    assets = pd.read_csv("model_dim/gis_assets.csv")

    print(f"{len(line)} line segments, {len(mileposts)} mileposts, "
          f"{len(assets)} assets (MP {assets.milepost_start.min()} to "
          f"{assets.milepost_end.max()})\n")

    route = pick_route(line, mileposts)
    print(f"\nusing the {route.length / MILE:.2f} mi piece")

    anchor_table = anchors(mileposts, route)
    print(f"{len(anchor_table)} mileposts on it "
          f"(MP {anchor_table.MILEPOST.min()} to {anchor_table.MILEPOST.max()})")

    assets["start_m"] = assets.milepost_start.apply(locate, anchor_table=anchor_table)
    assets["end_m"] = assets.milepost_end.apply(locate, anchor_table=anchor_table)

    points = assets[assets.location_type == "Point"].copy()
    points["geometry"] = points.start_m.apply(route.interpolate)

    lines = assets[assets.location_type == "Linear"].copy()
    lines["geometry"] = [substring(route, min(a, b), max(a, b))
                         for a, b in zip(lines.start_m, lines.end_m)]

    points = gpd.GeoDataFrame(points, geometry="geometry", crs=METRES)
    lines = gpd.GeoDataFrame(lines, geometry="geometry", crs=METRES)

    checks = [
        ("points sit on the route",
         points.geometry.apply(route.distance).max() < 0.01),
        ("all assets placed",
         len(points) + len(lines) == len(assets)),
        ("cost preserved",
         round(points.total_cost.sum() + lines.total_cost.sum(), 2)
         == round(assets.total_cost.sum(), 2)),
    ]
    print()
    for name, passed in checks:
        print(f"  {'ok  ' if passed else 'FAIL'} {name}")

    # the workbook says 17.5 track miles each, worked out with no reference to
    # any of this, so the two should land close
    span = ((lines.end_m - lines.start_m).abs() / MILE).round(2).tolist()
    print(f"  linear asset lengths: {span} mi (workbook says 17.5)")

    out = "asset_inventory.gpkg"
    points.drop(columns=["start_m", "end_m"]).to_crs(4326).to_file(
        out, layer="assets_point", driver="GPKG")
    lines.drop(columns=["start_m", "end_m"]).to_crs(4326).to_file(
        out, layer="assets_linear", driver="GPKG")
    gpd.GeoDataFrame({"name": ["Hanover Subdivision"]}, geometry=[route],
                     crs=METRES).to_crs(4326).to_file(
        out, layer="route", driver="GPKG")

    print(f"\n{len(points)} points + {len(lines)} lines -> {out}")


if __name__ == "__main__":
    main()