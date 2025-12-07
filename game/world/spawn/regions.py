# AUTHORED BY: Scott Petty

import random, math
from typing import Dict, Tuple, List, Optional

def sample_point(regions: Dict, name: Optional[str]) -> Tuple[int, int]:
    if not name or name not in regions:
        return _fallback()
    r = regions[name]
    t = r.get("type")
    if t == "rect":
        x, y, w, h = r.get("x", 0), r.get("y", 0), r.get("w", 1), r.get("h", 1)
        return random.randint(int(x), int(x+w)), random.randint(int(y), int(y+h))
    if t == "ring":
        cx, cy = r.get("center", [0, 0])
        rmin, rmax = r.get("r_min", 0), r.get("r_max", max(1, r.get("r_min", 1)+1))
        u, ang = random.random(), random.random()*2*math.pi
        rad = math.sqrt((rmax*rmax - rmin*rmin) * u + rmin*rmin)
        return int(cx + rad*math.cos(ang)), int(cy + rad*math.sin(ang))
    if t == "poly":
        pts = r.get("points") or []
        if len(pts) < 3: return _fallback()
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        minx, maxx, miny, maxy = int(min(xs)), int(max(xs)), int(min(ys)), int(max(ys))
        for _ in range(32):
            x = random.randint(minx, maxx); y = random.randint(miny, maxy)
            if _point_in_poly(x, y, pts): return x, y
    return _fallback()

def _point_in_poly(x: int, y: int, poly: List[List[int]]) -> bool:
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % len(poly)]
        if ((y1 > y) != (y2 > y)) and (x < (x2-x1) * (y-y1) / (y2-y1 + 1e-9) + x1):
            inside = not inside
    return inside

def _fallback() -> Tuple[int, int]:
    return random.randint(96, 320), random.randint(80, 200)
