# Paso 4: genera las líneas addr:interpolation, una por cuadra y por lado.
# Para cada calle con nombre de OSM: se muestrea cada 2 m, se ubica cada punto en el
# mapa, se decide si la cuadra corre norte-sur o este-oeste y en qué centena cae.
# Cada tramo de una misma centena genera dos líneas a 6 m de la calle: pares a la
# derecha y impares a la izquierda, en el sentido en que crecen las alturas.
# Salida: lineas.json
# Autor: Matias Millan
import json, math, collections, re
import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union, substring, linemerge
from comun import cargar_osm, xy_nodo, a_lonlat, transformacion

d, N, W = cargar_osm('osm.json')
a_mapa = transformacion()[1]
bd = json.load(open('bandas.json'))

def bordes(T):
    T = sorted(T); ys = [t[0] for t in T]; e = []
    for i, (y, h) in enumerate(T):
        lo = (ys[i - 1] + y) / 2 if i > 0 else y - (ys[1] - ys[0]) / 2
        hi = (ys[i + 1] + y) / 2 if i < len(T) - 1 else y + (ys[-1] - ys[-2]) / 2
        e.append((min(lo, hi), max(lo, hi), h))
    return e
VE, HE = bordes(bd['VT']), bordes(bd['HT'])

def altura(v, E, crece):
    for lo, hi, h in E:
        if lo <= v <= hi:
            f = (v - lo) / (hi - lo); return h, (f if crece else 1 - f)
    return None, None

# Manzanas del mapa (relleno gris) para saber de qué lado de la calle hay frentistas
polys = []
for f in json.load(open('pdf_rellenos.json')):
    c = f['fill']
    if not (len(c) == 3 and 0.72 <= c[0] <= 0.84 and abs(c[0] - c[2]) < 0.03): continue
    pts = [tuple(pt) for it in f['items'] for pt in it[1:] if isinstance(pt, list) and len(pt) == 2]
    if len(pts) >= 3:
        P = Polygon(pts)
        if not P.is_valid: P = P.buffer(0)
        if P.area > 20: polys.append(P)
manzanas = unary_union(polys).buffer(2.0)

existentes = [LineString([xy_nodo(N, n) for n in w['nodes']]) for w in W.values() if 'addr:interpolation' in w.get('tags', {}) and all(n in N for n in w['nodes'])]
existU = unary_union(existentes).buffer(20) if existentes else None
HW = {'residential', 'secondary', 'tertiary', 'unclassified', 'living_street', 'primary'}
pornombre = collections.defaultdict(list)
for w in W.values():
    t = w.get('tags', {})
    if t.get('highway') not in HW or not t.get('name') or not all(n in N for n in w['nodes']): continue
    if re.search(r'Ruta|Via de servicio|Pública', t['name']): continue
    pornombre[t['name']].append(LineString([xy_nodo(N, n) for n in w['nodes']]))
items = []
for nm, v in pornombre.items():
    mg = linemerge(v); partes = [mg] if mg.geom_type == 'LineString' else list(mg.geoms)
    items += [(nm, f'{nm}#{i}', p) for i, p in enumerate(partes)]
HWBUF = unary_union([LineString([xy_nodo(N, n) for n in w['nodes']]) for w in W.values()
                     if w.get('tags', {}).get('highway') in ('residential', 'secondary', 'tertiary', 'unclassified', 'living_street', 'primary', 'trunk', 'service', 'pedestrian', 'track')
                     and all(n in N for n in w['nodes'])]).buffer(4.5)

lineas = []; descartes = collections.Counter()
for nm, wid, L in items:
    if L.length < 30: continue
    muestras = []
    for i in range(int(L.length // 2.0) + 2):
        s = min(i * 2.0, L.length); p = L.interpolate(s)
        a = L.interpolate(max(s - 8, 0)); b = L.interpolate(min(s + 8, L.length))
        dx, dy = a_mapa((b.x, b.y)) - a_mapa((a.x, a.y)); ang = math.degrees(math.atan2(dy, dx)) % 180
        q = a_mapa((p.x, p.y))
        if 70 < ang < 110: o = 'V'; h, _ = altura(q[1], VE, False)
        elif ang < 20 or ang > 160: o = 'H'; h, _ = altura(q[0], HE, True)
        else: o = 'D'; h = None
        muestras.append((s, o, h))
    tramos = []; cur = None
    for s, o, h in muestras:
        if cur and cur[0] == (o, h): cur[2] = s
        else:
            if cur: tramos.append(cur)
            cur = [(o, h), s, s]
    if cur: tramos.append(cur)
    for (o, h), s0, s1 in tramos:
        if o == 'D' or h is None: descartes['diagonal/fuera']+= 1; continue
        if s1 - s0 < 35: descartes['tramo corto']+= 1; continue
        base = substring(L, s0 + 6, s1 - 6)
        if base.length < 20: continue
        qa, qb = a_mapa(base.coords[0]), a_mapa(base.coords[-1])
        if not ((qb[1] < qa[1]) if o == 'V' else (qb[0] > qa[0])): base = LineString(list(base.coords)[::-1])
        for paridad, signo in (('even', -1), ('odd', 1)):  # offset positivo = izquierda
            Lo = base.offset_curve(signo * 6.0, join_style='mitre')
            if Lo.geom_type != 'LineString' or Lo.length < 15: continue
            Lc = Lo.difference(HWBUF)
            if Lc.is_empty: descartes['recortada entera'] += 1; continue
            Lc = max(getattr(Lc, 'geoms', [Lc]), key=lambda g: g.length)
            if Lc.geom_type != 'LineString' or Lc.length < 15: descartes['recortada corta'] += 1; continue
            if (Lc.coords[0] != Lo.coords[0] or Lc.coords[-1] != Lo.coords[-1]) and Point(Lc.coords[0]).distance(Point(Lo.coords[-1])) < Point(Lc.coords[0]).distance(Point(Lo.coords[0])):
                Lc = LineString(list(Lc.coords)[::-1])
            Lo = Lc
            chk = [Lo.interpolate(fr, normalized=True) for fr in (0.25, 0.5, 0.75)]
            if sum(manzanas.contains(Point(*a_mapa((c.x, c.y)))) for c in chk) < 2: descartes['sin manzana de ese lado'] += 1; continue
            if existU is not None and existU.contains(Lo.interpolate(0.5, normalized=True)): descartes['ya tiene numeración'] += 1; continue
            mid = Lo.interpolate(0.5, normalized=True)
            if any(o2.distance(mid) < 9 for o2 in pornombre[nm] if o2.distance(base.interpolate(0.5, normalized=True)) > 3): descartes['cantero central'] += 1; continue
            def num(p):
                q = a_mapa(p); return altura(q[1], VE, False) if o == 'V' else altura(q[0], HE, True)
            ha, fa = num(Lo.coords[0]); hb, fb = num(Lo.coords[-1])
            if ha != h or hb != h: fa = fa if ha == h else 0.0; fb = fb if hb == h else 1.0
            a = h + int(round(fa * 100)); b = h + int(round(fb * 100))
            if paridad == 'even': a += a % 2; b -= b % 2; a = max(a, h); b = min(b, h + 98)
            else: a += 1 - a % 2; b -= 1 - b % 2; a = max(a, h + 1); b = min(b, h + 99)
            if b <= a: descartes['rango vacío'] += 1; continue
            if Lo.coords[0] == Lo.coords[-1]: continue
            Ls = Lo.simplify(0.5)
            lineas.append({'street': nm, 'parity': paridad, 'from': a, 'to': b, 'coords': [a_lonlat(c) for c in Ls.coords], 'way': wid, 'len': round(Ls.length)})

# Zonas excluidas: barrio Solares de Villa (numeración propia), Parque Industrial MLF
# (este) y calles al sur de la avenida (el mapa no trae su regla de alturas).
H = sorted([((s['bbox'][0] + s['bbox'][2]) / 2, (s['bbox'][1] + s['bbox'][3]) / 2) for s in json.load(open('pdf_textos.json'))
            if 150 < s['bbox'][1] < 900 and re.fullmatch(r'\d{1,4}', s['t']) and abs(s['dir'][0]) > 0.5])
xs = [h[0] for h in H]; ys = [h[1] for h in H]
solares = Polygon([(-63.5545, -31.5553), (-63.5486, -31.5553), (-63.5486, -31.5620), (-63.5545, -31.5620)])
from comun import a_xy
quedan = []; fuera = collections.Counter()
for l in lineas:
    mid = l['coords'][len(l['coords']) // 2]
    if solares.contains(Point(mid)): fuera['Solares de Villa'] += 1; continue
    if mid[0] > -63.5235: fuera['Parque Industrial MLF'] += 1; continue
    q = a_mapa(a_xy(*mid))
    if q[1] > float(np.interp(q[0], xs, ys)) - 4: fuera['sur de la avenida'] += 1; continue
    quedan.append(l)
json.dump(quedan, open('lineas.json', 'w'), ensure_ascii=False)
print('generadas', len(lineas), 'descartes', dict(descartes)); print('zonas excluidas', dict(fuera))
print('líneas finales', len(quedan), 'calles', len({l["street"] for l in quedan}))
