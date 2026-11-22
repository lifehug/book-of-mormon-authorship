"""BOM-116, second design: the earth the window counter reads (open physical data only).

Global rasters at ``lab.geography2.earth.raster_deg`` (0.05 degrees, about 5.5 km), built once
from files fetched by ``lab.sources`` (group ``physical``) and cached under
``data/corpus/lab/geography2/``:

- **water**: not land in Natural Earth 1:10m (public domain), plus Natural Earth lakes at least
  ``lake_min_km2`` in area. "Sea" in a text is any of this water (the Bible's "salt sea" is a lake).
- **elevation**: ETOPO 2022 at 60 arc-seconds (NOAA, public domain), mean of each 3 x 3 block.
- **distance to water** along each of the 8 compass directions, in km, from every pixel (capped).
  From these come "the sea lies west of A within d km" and the width of a neck of land along an
  axis (distance to water one way plus the other way) with land continuing across it.
- **rivers**: Natural Earth 1:10m river and lake centre-lines, grouped by name; the head is the
  end with the higher ETOPO elevation and the mouth the lower (HydroRIVERS is not used: its
  licence forbids redistribution as a stand-alone product).
- **coastline age** (AGE 2021, University of Amsterdam, CC BY 4.0): pixels of today's sea that
  were land within the last ``age_recent_ka`` thousand years, counted per window as a check on
  using the modern coast.

Then :func:`window` turns a disc of the earth into a grid of cells with pooled features, and
:func:`solve` asks whether some layout of a text's places on those cells meets every feature.
No text is read here.

Usage: imported by ``lab.geography2`` (``python -m lab.geography2 earth`` builds the cache).
"""

from __future__ import annotations

import json
import math
import struct
import zipfile
import zlib
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from lab.paths import FAST, out

PHYS = FAST / "sources" / "physical"
CACHE = FAST / "geography2"
EARTH_KM = 6371.0
KM_DEG = math.pi * EARTH_KM / 180.0
# The 8 compass directions as (row step, column step) on a north-up raster, clockwise from N.
DIRS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
STEPS = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))
BEARING = {d: 45.0 * i for i, d in enumerate(DIRS)}


# --------------------------------------------------------------------------- reading the files


def read_tiff_float(path: Path) -> np.ndarray:
    """A tiled, deflate-compressed float32 GeoTIFF with the floating-point predictor (ETOPO
    2022's own format), read with numpy and zlib only."""
    with path.open("rb") as f:
        head = f.read(8)
        bo = "<" if head[:2] == b"II" else ">"
        f.seek(struct.unpack(bo + "I", head[4:8])[0])
        n = struct.unpack(bo + "H", f.read(2))[0]
        tags = {}
        for _ in range(n):
            tag, typ, cnt, val = struct.unpack(bo + "HHI4s", f.read(12))
            size = {3: 2, 4: 4, 12: 8}.get(typ, 1)
            fmt = {3: "H", 4: "I", 12: "d"}.get(typ, "B")
            if cnt * size <= 4:
                tags[tag] = struct.unpack(bo + fmt * cnt, val[: cnt * size])
            else:
                here = f.tell()
                f.seek(struct.unpack(bo + "I", val)[0])
                tags[tag] = struct.unpack(bo + fmt * cnt, f.read(cnt * size))
                f.seek(here)
        width, height = tags[256][0], tags[257][0]
        if tags[258][0] != 32 or tags[259][0] not in (8, 32946) or tags[339][0] != 3:
            raise ValueError("not a deflate float32 TIFF")
        tw, th = tags[322][0], tags[323][0]
        predictor = tags.get(317, (1,))[0]
        offsets, counts = tags[324], tags[325]
        across = (width + tw - 1) // tw
        img = np.empty((height, width), dtype=np.float32)
        for i, (o, c) in enumerate(zip(offsets, counts, strict=True)):
            f.seek(o)
            raw = np.frombuffer(zlib.decompress(f.read(c)), dtype=np.uint8)
            if predictor == 3:
                b = raw.reshape(th, 4 * tw).cumsum(axis=1, dtype=np.uint8)
                tile = b.reshape(th, 4, tw).transpose(0, 2, 1).copy().view(">f4")[..., 0]
            else:
                tile = raw.view(bo + "f4").reshape(th, tw)
            r, c0 = (i // across) * th, (i % across) * tw
            h, w = min(th, height - r), min(tw, width - c0)
            img[r : r + h, c0 : c0 + w] = tile[:h, :w]
    return img


def polygons(path: Path) -> list[tuple[list[np.ndarray], dict]]:
    """Each polygon of a GeoJSON file as its rings (arrays of lon, lat) and properties."""
    got = []
    for feat in json.loads(path.read_text())["features"]:
        g = feat["geometry"]
        if g is None:
            continue
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        if g["type"] not in ("Polygon", "MultiPolygon"):
            continue
        for poly in polys:
            got.append(([np.asarray(r, dtype=float)[:, :2] for r in poly], feat["properties"]))
    return got


def ring_area_km2(ring: np.ndarray) -> float:
    lon, lat = ring[:, 0], ring[:, 1]
    x = np.radians(lon) * EARTH_KM * np.cos(np.radians(lat.mean()))
    y = np.radians(lat) * EARTH_KM
    return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))) / 2.0


def rasterize(polys: list[list[np.ndarray]], res: float) -> np.ndarray:
    """Even-odd fill of polygons (rings as lon, lat) on a global north-up grid of ``res``
    degrees; a pixel is inside when its centre is."""
    h, w = int(round(180 / res)), int(round(360 / res))
    rows, xs = [], []
    for rings in polys:
        for ring in rings:
            x = (ring[:, 0] + 180.0) / res
            y = (90.0 - ring[:, 1]) / res
            x0, y0, x1, y1 = x[:-1], y[:-1], x[1:], y[1:]
            lo = np.ceil(np.minimum(y0, y1) - 0.5).astype(int)
            hi = np.ceil(np.maximum(y0, y1) - 0.5).astype(int)  # rows lo .. hi-1
            n = np.maximum(hi - lo, 0)
            if not n.any():
                continue
            e = np.repeat(np.arange(len(n)), n)
            r = lo[e] + (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n))
            yc = r + 0.5
            t = (yc - y0[e]) / (y1[e] - y0[e])
            rows.append(r)
            xs.append(x0[e] + t * (x1[e] - x0[e]))
    mark = np.zeros((h, w + 1), dtype=np.uint8)
    if rows:
        r = np.concatenate(rows)
        c = np.clip(np.ceil(np.concatenate(xs) - 0.5).astype(int), 0, w)
        ok = (r >= 0) & (r < h)
        np.add.at(mark, (r[ok], c[ok]), 1)
    inside = np.empty((h, w), dtype=bool)
    for a in range(0, h, 400):
        inside[a : a + 400] = (np.cumsum(mark[a : a + 400, :w], axis=1) % 2).astype(bool)
    return inside


def directional_distance(water: np.ndarray, res: float, cap_km: float) -> np.ndarray:
    """For every pixel and each of the 8 directions, km to the first water pixel along that
    direction (``cap_km`` when none within it); 0 on water. East-west wraps around the globe."""
    h, w = water.shape
    lat = 90.0 - (np.arange(h) + 0.5) * res
    ns_km = res * KM_DEG
    ew_km = res * KM_DEG * np.cos(np.radians(lat))[:, None]
    big = np.iinfo(np.int32).max // 2
    outd = np.empty((8, h, w), dtype=np.float32)

    def run(arr: np.ndarray) -> np.ndarray:
        """Index steps to the next True along axis 1, looking toward increasing index."""
        n = arr.shape[1]
        idx = np.where(arr, np.arange(n)[None, :], big)
        nxt = np.minimum.accumulate(idx[:, ::-1], axis=1)[:, ::-1]
        return (nxt - np.arange(n)[None, :]).astype(np.float64)

    # E and W, with wrap: lay the globe twice side by side.
    two = np.concatenate([water, water], axis=1)
    east = run(two)[:, :w]
    west = run(two[:, ::-1])[:, :w][:, ::-1]
    north = run(water[::-1].T).T[::-1]  # toward smaller row
    south = run(water.T).T
    for d, steps, unit in (
        ("E", east, ew_km),
        ("W", west, ew_km),
        ("N", north, ns_km),
        ("S", south, ns_km),
    ):
        outd[DIRS.index(d)] = np.minimum(steps * unit, cap_km)
    # Diagonals: skew so that each diagonal line is one column of a (h, w + h) array.
    diag_km = np.sqrt(ns_km**2 + ew_km**2)
    for d in ("NE", "SE", "SW", "NW"):
        dr, dc = STEPS[DIRS.index(d)]
        sk = np.ones((h, w + h), dtype=bool)  # outside the grid counts as water (no wrap)
        r = np.arange(h)[:, None]
        cols = np.arange(w)[None, :] + (r if dr * dc < 0 else (h - 1 - r))
        sk[np.broadcast_to(r, (h, w)), cols] = water
        # moving (dr, dc) keeps the skewed column and moves the row by dr
        steps = run(sk[::-1].T).T[::-1] if dr < 0 else run(sk.T).T
        outd[DIRS.index(d)] = np.minimum(steps[np.broadcast_to(r, (h, w)), cols] * diag_km, cap_km)
    outd[:, water] = 0.0
    return outd


def read_age(path: Path, res: float, recent: float) -> np.ndarray:
    """Pixels (at ``res``) of the AGE 2021 tiles drowned within the last ``recent`` thousand
    years: land then, sea now. The archive is read in memory, never unpacked."""
    h, w = int(round(180 / res)), int(round(360 / res))
    got = np.zeros((h, w), dtype=bool)
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".asc"):
                continue
            lines = z.read(name).decode().split("\n")
            meta = {ln.split()[0].upper(): float(ln.split()[1]) for ln in lines[:6]}
            grid = np.loadtxt(lines[6:], dtype=np.float32, ndmin=2)
            ncols, cell = int(meta["NCOLS"]), meta["CELLSIZE"]
            nrows = grid.shape[0]
            lon = meta["XLLCORNER"] + (np.arange(ncols) + 0.5) * cell
            lat = meta["YLLCORNER"] + (nrows - np.arange(nrows) - 0.5) * cell
            hit = (grid > 0) & (grid <= recent * 10)  # values: age in units of 0.1 ka
            rr, cc = np.nonzero(hit)
            r = ((90.0 - lat[rr]) / res).astype(int)
            c = ((lon[cc] + 180.0) / res).astype(int) % w
            ok = (r >= 0) & (r < h)
            got[r[ok], c[ok]] = True
    return got


def build(cfg: dict) -> dict:
    """Build the global rasters and the river table; returns counts (no text)."""
    e = cfg["lab"]["geography2"]["earth"]
    res = e["raster_deg"]
    land = rasterize([p for p, _ in polygons(PHYS / "ne_10m_land.geojson")], res)
    lakes_all = polygons(PHYS / "ne_10m_lakes.geojson")
    big = [p for p, _ in lakes_all if ring_area_km2(p[0]) >= e["lake_min_km2"]]
    lakes = rasterize(big, res)
    water = ~land | lakes
    tif = read_tiff_float(PHYS / "ETOPO_2022_v1_60s_N90W180_surface.tif")
    k = int(round(res * 60))
    hh, ww = tif.shape[0] // k, tif.shape[1] // k
    elev = tif[: hh * k, : ww * k].reshape(hh, k, ww, k).mean(axis=(1, 3)).astype(np.float32)
    del tif
    dist = directional_distance(water, res, e["cap_km"])
    age = read_age(PHYS / "age_2021_coastline_age" / "AGE_tiles.zip", res, e["age_recent_ka"])
    np.savez(  # path from out(
        out(CACHE / "earth.npz"),
        water=water,
        elev=elev,
        dist=dist.astype(np.float16),
        age_recent=age & water,
    )
    rivers = river_table(PHYS / "ne_10m_rivers_lake_centerlines.geojson", elev, res)
    out(CACHE / "rivers.json").write_text(json.dumps(rivers))
    meta = {
        "raster_deg": res,
        "shape": list(water.shape),
        "land_share": round(float(land.mean()), 4),
        "lakes_used": len(big),
        "lakes_in_file": len(lakes_all),
        "rivers": len(rivers),
        "recently_drowned_pixels": int((age & water).sum()),
    }
    out(CACHE / "earth.json").write_text(json.dumps(meta, indent=1))
    return meta


def sample_elev(elev: np.ndarray, res: float, lat, lon) -> np.ndarray:
    r = np.clip(((90.0 - np.asarray(lat)) / res).astype(int), 0, elev.shape[0] - 1)
    c = ((np.asarray(lon) + 180.0) / res).astype(int) % elev.shape[1]
    return elev[r, c]


def river_table(path: Path, elev: np.ndarray, res: float) -> list[dict]:
    """Rivers grouped by name (unnamed segments each their own river): vertices, head (the end
    with the highest elevation) and mouth (the lowest)."""
    groups: dict[str, list[np.ndarray]] = {}
    for i, feat in enumerate(json.loads(path.read_text())["features"]):
        g, p = feat["geometry"], feat["properties"]
        if g is None or g["type"] not in ("LineString", "MultiLineString"):
            continue
        lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        name = (p.get("name") or p.get("name_en") or "").strip() or f"unnamed_{i}"
        for ln in lines:
            groups.setdefault(name, []).append(np.asarray(ln, dtype=float)[:, :2])
    rivers = []
    for name, lines in sorted(groups.items()):
        ends = np.array([pt for ln in lines for pt in (ln[0], ln[-1])])
        z = sample_elev(elev, res, ends[:, 1], ends[:, 0])
        head, mouth = ends[int(np.argmax(z))], ends[int(np.argmin(z))]
        verts = np.concatenate(lines)
        rivers.append(
            {
                "name": name,
                "head": head.round(4).tolist(),
                "mouth": mouth.round(4).tolist(),
                "head_m": float(z.max()),
                "mouth_m": float(z.min()),
                "lon": verts[:, 0].round(4).tolist(),
                "lat": verts[:, 1].round(4).tolist(),
            }
        )
    return rivers


# --------------------------------------------------------------------------- geometry


def destination(lat0, lon0, bearing_deg, dist_km):
    """Points at ``dist_km`` along ``bearing_deg`` from (lat0, lon0) on the sphere."""
    p1, l1 = math.radians(lat0), math.radians(lon0)
    b, d = np.radians(bearing_deg), np.asarray(dist_km) / EARTH_KM
    p2 = np.arcsin(np.sin(p1) * np.cos(d) + np.cos(p1) * np.sin(d) * np.cos(b))
    l2 = l1 + np.arctan2(np.sin(b) * np.sin(d) * np.cos(p1), np.cos(d) - np.sin(p1) * np.sin(p2))
    return np.degrees(p2), (np.degrees(l2) + 540.0) % 360.0 - 180.0


def dist_bearing(lat1, lon1, lat2, lon2):
    """Great-circle km and initial bearing (degrees) from point 1 to point 2 (broadcasting)."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(lon2) - np.radians(lon1)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    d = 2 * EARTH_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    y = np.sin(dl) * np.cos(p2)
    x = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    return d, (np.degrees(np.arctan2(y, x)) + 360.0) % 360.0


def in_cone(bearing, centre_deg, cone_deg) -> np.ndarray:
    return np.abs((np.asarray(bearing) - centre_deg + 180.0) % 360.0 - 180.0) <= cone_deg


class Earth:
    """The cached rasters and rivers, with window sampling."""

    def __init__(self, cfg: dict, cache: Path = CACHE):
        e = cfg["lab"]["geography2"]["earth"]
        z = np.load(cache / "earth.npz")
        self.res = e["raster_deg"]
        self.water, self.elev = z["water"], z["elev"]
        self.dist = z["dist"]
        self.age_recent = z["age_recent"]
        self.e = e
        self.rivers = json.loads((cache / "rivers.json").read_text())
        self.r_lat = np.concatenate([np.asarray(r["lat"]) for r in self.rivers])
        self.r_lon = np.concatenate([np.asarray(r["lon"]) for r in self.rivers])
        self.r_id = np.concatenate([np.full(len(r["lat"]), i) for i, r in enumerate(self.rivers)])
        self.r_tree = cKDTree(unit(self.r_lat, self.r_lon))

    @classmethod
    def from_arrays(cls, cfg: dict, water, elev, dist, rivers, age_recent=None) -> Earth:
        """An earth built in memory (tests and hand-made worlds)."""
        self = cls.__new__(cls)
        e = cfg["lab"]["geography2"]["earth"]
        self.res, self.e = e["raster_deg"], e
        self.water, self.elev, self.dist = water, elev, dist
        self.age_recent = age_recent if age_recent is not None else np.zeros_like(water)
        self.rivers = rivers
        if rivers:
            self.r_lat = np.concatenate([np.asarray(r["lat"]) for r in rivers])
            self.r_lon = np.concatenate([np.asarray(r["lon"]) for r in rivers])
            self.r_id = np.concatenate([np.full(len(r["lat"]), i) for i, r in enumerate(rivers)])
            self.r_tree = cKDTree(unit(self.r_lat, self.r_lon))
        else:
            self.r_tree = None
        return self

    def pix(self, lat, lon):
        r = np.clip(((90.0 - np.asarray(lat)) / self.res).astype(int), 0, self.water.shape[0] - 1)
        c = ((np.asarray(lon) + 180.0) / self.res).astype(int) % self.water.shape[1]
        return r, c

    def is_water(self, lat, lon) -> np.ndarray:
        return self.water[self.pix(lat, lon)]

    def elevation(self, lat, lon) -> np.ndarray:
        return self.elev[self.pix(lat, lon)].astype(float)

    def water_dist(self, lat, lon) -> np.ndarray:
        """(8, n) km to water along each direction from each point."""
        r, c = self.pix(lat, lon)
        return self.dist[:, r, c].astype(float)


def unit(lat, lon) -> np.ndarray:
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)


def chord(km: float) -> float:
    return 2 * math.sin(km / EARTH_KM / 2)


# --------------------------------------------------------------------------- windows


def window(earth: Earth, lat0: float, lon0: float, diameter: float, w: dict) -> dict:
    """A disc of the earth as a grid of cells (north-up), each with pooled features.

    Per cell: ``land`` / ``water`` (some sample is), ``elev`` (mean over land samples),
    ``sea[8]`` (least km to water along each earth direction over land samples), ``neck[4]``
    (least width across each earth axis N-S, NE-SW, E-W, SE-NW over land samples whose land
    continues at least ``neck_land_frac`` of the radius both ways along the other axis).
    """
    g = w["grid"]
    cell = diameter / g
    ax = (np.arange(g) - (g - 1) / 2) * cell
    u, v = np.meshgrid(ax, ax[::-1])
    keep = np.hypot(u, v) <= diameter / 2 + 1e-9
    u, v = u[keep], v[keep]
    n = len(u)
    rho, beta = np.hypot(u, v), np.degrees(np.arctan2(u, v))
    clat, clon = destination(lat0, lon0, beta, rho)
    s = int(min(w["samples_max"], max(2, math.ceil(cell / (earth.res * KM_DEG)))))
    off = ((np.arange(s) + 0.5) / s - 0.5) * cell
    du, dv = np.meshgrid(off, off)
    su = (u[:, None] + du.ravel()[None, :]).ravel()
    sv = (v[:, None] + dv.ravel()[None, :]).ravel()
    slat, slon = destination(lat0, lon0, np.degrees(np.arctan2(su, sv)), np.hypot(su, sv))
    r, c = earth.pix(slat, slon)
    wat = earth.water[r, c].reshape(n, s * s)
    lnd = ~wat
    el = earth.elev[r, c].astype(float).reshape(n, s * s)
    dist = earth.dist[:, r, c].astype(float).reshape(8, n, s * s)
    with np.errstate(invalid="ignore"):
        elev = np.where(lnd.any(1), np.nansum(np.where(lnd, el, 0), 1) / lnd.sum(1), np.nan)
    sea = np.where(lnd[None], dist, np.inf).min(axis=2)
    need = w["neck_land_frac"] * diameter / 2
    neck = np.full((4, n), np.inf)
    for a in range(4):
        width = dist[a] + dist[a + 4] + earth.res * KM_DEG
        across = np.minimum(dist[(a + 2) % 8], dist[(a + 6) % 8])
        ok = (
            lnd
            & (across >= need)
            & (dist[a] < earth.e["cap_km"])
            & (dist[a + 4] < earth.e["cap_km"])
        )
        neck[a] = np.where(ok, width, np.inf).min(axis=1)
    win = {
        "lat0": lat0,
        "lon0": lon0,
        "diameter": diameter,
        "cell_km": cell,
        "n": n,
        "lat": clat,
        "lon": clon,
        "land": lnd.any(1),
        "water": wat.any(1),
        "elev": elev,
        "sea": sea,
        "neck": neck,
        "recent_drowned": int(earth.age_recent[r, c].sum()),
    }
    d, b = dist_bearing(clat[:, None], clon[:, None], clat[None, :], clon[None, :])
    win["d"], win["b"] = d, b  # b[i, j]: bearing from cell i to cell j
    win["rivers"] = window_rivers(earth, win, w)
    return win


def window_rivers(earth: Earth, win: dict, w: dict) -> list[dict]:
    """Rivers with a vertex in the disc: which cells lie on them, hold their head, their mouth."""
    if earth.r_tree is None:
        return []
    lat0, lon0, rad = win["lat0"], win["lon0"], win["diameter"] / 2
    hits = earth.r_tree.query_ball_point(unit(lat0, lon0), chord(rad))
    ids = sorted(set(earth.r_id[hits].tolist()))
    tol = max(w["river_km"], win["cell_km"] * 0.75)
    ctree = cKDTree(unit(win["lat"], win["lon"]))
    got = []
    for i in ids:
        r = earth.rivers[i]
        pts = unit(np.asarray(r["lat"]), np.asarray(r["lon"]))
        near = np.zeros(win["n"], dtype=bool)
        for hit in ctree.query_ball_point(pts, chord(tol)):
            near[hit] = True
        if not near.any():
            continue
        head = np.zeros(win["n"], dtype=bool)
        mouth = np.zeros(win["n"], dtype=bool)
        head[ctree.query_ball_point(unit(r["head"][1], r["head"][0]), chord(tol))] = True
        mouth[ctree.query_ball_point(unit(r["mouth"][1], r["mouth"][0]), chord(tol))] = True
        _d, flow = dist_bearing(r["head"][1], r["head"][0], r["mouth"][1], r["mouth"][0])
        got.append(
            {"name": r["name"], "near": near, "head": head, "mouth": mouth, "flow": float(flow)}
        )
    return got


# --------------------------------------------------------------------------- the solver


def compile_features(feats: list[dict], win: dict, rot: int, w: dict) -> tuple | None:
    """Unary masks and binary tables for one window at rotation ``rot`` (the text's north is
    the earth's bearing ``45 * rot``). Returns (variables, domains, binary) or None when a
    variable has an empty domain before search."""
    n = win["n"]
    theta = 45.0 * rot
    places = sorted({f["a"] for f in feats if f.get("a")} | {f["b"] for f in feats if f.get("b")})
    rivers = sorted({f["river"] for f in feats if f.get("river")})
    var = [("p", p) for p in places] + [("r", r) for r in rivers]
    idx = {v: i for i, v in enumerate(var)}
    wr = win["rivers"]
    dom = []
    for kind, _name in var:
        dom.append(win["land"].copy() if kind == "p" else np.ones(len(wr), dtype=bool))
    water_places = {f["a"] for f in feats if f["kind"] == "water"}
    for p in water_places:
        dom[idx[("p", p)]] = win["water"].copy()
    binary: list[tuple[int, int, np.ndarray]] = []
    tol = win["cell_km"]
    sea_km = max(w["sea_km"], win["cell_km"] * 0.75)

    def earth_dir(frame_dir: str) -> int:
        return (DIRS.index(frame_dir) + rot) % 8

    for f in feats:
        k = f["kind"]
        if k == "water":
            continue
        if k == "sea":
            i = idx[("p", f["a"])]
            lim = max(f.get("max_km", sea_km), win["cell_km"] * 0.75)
            if f.get("side"):
                dom[i] &= win["sea"][earth_dir(f["side"])] <= lim
            else:
                dom[i] &= win["sea"].min(axis=0) <= lim
        elif k == "neck":
            i = idx[("p", f["a"])]
            width = f.get("width_km") or w["neck_max_km"]
            width = max(width, win["cell_km"] * 0.5)
            if f.get("water_sides"):
                axis = earth_dir(f["water_sides"].split("-")[0]) % 4
                dom[i] &= win["neck"][axis] <= width
            else:
                dom[i] &= win["neck"].min(axis=0) <= width
        elif k == "direction":
            i, j = idx[("p", f["a"])], idx[("p", f["b"])]
            m = in_cone(win["b"].T, theta + BEARING[f["dir"]], f["cone"]) & (win["d"] > 0)
            binary.append((i, j, m))  # m[x, y]: a at x, b at y, bearing from y to x in cone
        elif k == "higher":
            i, j = idx[("p", f["a"])], idx[("p", f["b"])]
            m = (win["elev"][:, None] - win["elev"][None, :]) > w["higher_margin_m"]
            binary.append((i, j, np.nan_to_num(m, nan=False).astype(bool)))
        elif k == "days":
            i, j = idx[("p", f["a"])], idx[("p", f["b"])]
            lo, hi = f["km"]
            binary.append((i, j, (win["d"] >= lo - tol) & (win["d"] <= hi + tol)))
        elif k == "near":
            i, j = idx[("p", f["a"])], idx[("p", f["b"])]
            binary.append((i, j, win["d"] <= w["near_km"] + tol))
        elif k == "river":
            ri, pi = idx[("r", f["river"])], idx[("p", f["a"])]
            role = {"source": "head", "mouth": "mouth"}.get(f["role"], "near")
            m = np.array([r[role] for r in wr], dtype=bool).reshape(len(wr), n)
            binary.append((ri, pi, m))
        elif k == "flows":
            ri = idx[("r", f["river"])]
            flows = np.array([r["flow"] for r in wr])
            dom[ri] &= in_cone(flows, theta + BEARING[f["toward"]], f["cone"])
        else:
            raise ValueError(k)
    if any(not d.any() for d in dom):
        return None
    return var, dom, binary


def solve(var, dom, binary, node_limit: int) -> str:
    """'pass' when some assignment meets every table, 'fail' when none does, 'undecided' when
    the search ran out of ``node_limit`` nodes (a state of its own, never counted as either)."""
    nv = len(var)
    # arcs[j]: (i, M) with M[x_j, x_i] true when the pair of values is allowed
    arcs: list[list[tuple[int, np.ndarray]]] = [[] for _ in range(nv)]
    for i, j, m in binary:
        arcs[i].append((j, m))
        arcs[j].append((i, m.T))

    def ac(d: list[np.ndarray], queue: list[int]) -> bool:
        """Arc consistency from the variables in ``queue``; False when a domain empties."""
        pending = set(queue)
        while pending:
            j = pending.pop()
            for i, m_ji in arcs[j]:
                new = d[i] & m_ji[d[j]].any(axis=0)
                if not new.any():
                    return False
                if (new != d[i]).any():
                    d[i] = new
                    pending.add(i)
        return True

    d0 = [x.copy() for x in dom]
    if not ac(d0, list(range(nv))):
        return "fail"
    nodes = [0]

    def search(d: list[np.ndarray]) -> str:
        free = [i for i in range(nv) if d[i].sum() > 1]
        if not free:
            return "pass" if consistent(d) else "fail"
        i = min(free, key=lambda k: (int(d[k].sum()), -len(arcs[k])))
        undecided = False
        for x in np.flatnonzero(d[i]):
            nodes[0] += 1
            if nodes[0] > node_limit:
                return "undecided"
            d2 = [y.copy() for y in d]
            d2[i] = np.zeros_like(d[i])
            d2[i][x] = True
            if ac(d2, [i]):
                r = search(d2)
                if r == "pass":
                    return "pass"
                if r == "undecided":
                    undecided = True
                    if nodes[0] > node_limit:
                        return "undecided"
        return "undecided" if undecided else "fail"

    def consistent(d: list[np.ndarray]) -> bool:
        x = [int(np.flatnonzero(v)[0]) for v in d]
        return all(bool(m[x[i], x[j]]) for i, j, m in binary)

    return search(d0)
