# Paso 2: georreferencia el mapa (esquemático) con una transformación de semejanza
# ajustada entre los nombres de calles del PDF y las calles de OSM, refinada por
# ICP (cada etiqueta se proyecta a su calle). Salida: afin.json
# Autor: Matias Millan
import json, math, re, unicodedata, difflib, collections
import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import linemerge
from comun import cargar_osm, xy_nodo

S = [s for s in json.load(open('pdf_textos.json')) if 150 < s['bbox'][1] < 960]
d, N, W = cargar_osm('osm.json')
calles = collections.defaultdict(list)
for w in W.values():
    t = w.get('tags', {})
    if t.get('highway') and t.get('name') and all(n in N for n in w['nodes']):
        calles[t['name']].append(LineString([xy_nodo(N, n) for n in w['nodes']]))

def norm(s):
    s = unicodedata.normalize('NFD', s.lower()); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'\b(dr|dra|agrim|agrimensor|gral|gdor|gobernador|mnor|monsenor|hno|hnos|hermanos|hermanas|hnas|sta|santa|sgo|sargento|fco|ing|cro|av|avenida|bv|boulevard|bulevar|pje|pasaje)\b\.?', '', s)
    return re.sub(r'[^a-z0-9 ]', '', s).strip()

on = {norm(k): k for k in calles}
pares = []
for s in S:
    t = s['t']
    if re.fullmatch(r'\d+', t) or len(t) < 4: continue
    m = difflib.get_close_matches(norm(t), list(on), n=1, cutoff=0.88)
    if m:
        x0, y0, x1, y1 = s['bbox']; pares.append((t, on[m[0]], ((x0 + x1) / 2, (y0 + y1) / 2)))
cnt = collections.Counter(p[1] for p in pares)
geoms = {nm: linemerge(calles[nm]) for nm in cnt}

def ajustar(a, b):
    ma, mb = a.mean(0), b.mean(0); A = (a - ma) * np.array([1, -1]); B = b - mb  # el PDF tiene y hacia abajo
    U, Sv, Vt = np.linalg.svd(A.T @ B); R = (U @ Vt).T
    if np.linalg.det(R) < 0: Vt[1] *= -1; R = (U @ Vt).T
    s = Sv.sum() / (A ** 2).sum()
    return (lambda p: (np.atleast_2d(p) - ma) * np.array([1, -1]) @ (s * R).T + mb), s, math.degrees(math.atan2(R[1, 0], R[0, 0]))

src = np.array([c for t, nm, c in pares if cnt[nm] == 1])
dst = np.array([(geoms[nm].centroid.x, geoms[nm].centroid.y) for t, nm, c in pares if cnt[nm] == 1])
T, s, rot = ajustar(src, dst)
P = np.array([p[2] for p in pares])
for _ in range(15):
    Q = T(P)
    tgt = np.array([(lambda g, q: (lambda pt: (pt.x, pt.y))(g.interpolate(g.project(Point(q)))))(geoms[nm], q) for (t, nm, c), q in zip(pares, Q)])
    res = np.linalg.norm(Q - tgt, axis=1); keep = res < np.percentile(res, 80)
    T, s, rot = ajustar(P[keep], tgt[keep])
res = np.array([geoms[nm].distance(Point(q)) for (t, nm, c), q in zip(pares, T(P))])
print('etiquetas', len(pares), 'escala m/pt', round(s, 3), 'rotación', round(rot, 2), 'residuo mediana m', round(float(np.median(res)), 1), 'p80', round(float(np.percentile(res, 80)), 1))
json.dump(T(np.array([[0, 0], [1, 0], [0, 1]])).tolist(), open('afin.json', 'w'))
