# Paso 5: controles de calidad.
#  a) ninguna línea generada toca o cruza una calle;
#  b) las direcciones reales ya cargadas en OSM caen en la centena que da el mapa;
#  c) las direcciones reales respetan "pares a la derecha en el sentido creciente".
# Autor: Matias Millan
import json, math, collections
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from comun import cargar_osm, xy_nodo, a_xy, transformacion

d, N, W = cargar_osm('osm.json')
a_mapa = transformacion()[1]
L = json.load(open('lineas.json'))
G = [LineString([a_xy(*c) for c in l['coords']]) for l in L]
hw = unary_union([LineString([xy_nodo(N, n) for n in w['nodes']]) for w in W.values()
                  if w.get('tags', {}).get('highway') in ('residential', 'secondary', 'tertiary', 'unclassified', 'living_street', 'primary', 'trunk', 'service') and all(n in N for n in w['nodes'])])
print('a) líneas que tocan o cruzan una calle:', sum(g.intersects(hw) for g in G))

bd = json.load(open('bandas.json'))
calles = collections.defaultdict(list)
for w in W.values():
    t = w.get('tags', {})
    if t.get('highway') and t.get('name') and all(n in N for n in w['nodes']): calles[t['name']].append(LineString([xy_nodo(N, n) for n in w['nodes']]))
interp = set(n for w in W.values() if 'addr:interpolation' in w.get('tags', {}) for n in w['nodes'])
ok_c = mal_c = 0; lados = collections.Counter(); filas = []
for e in d:
    t = e.get('tags', {}); hn = t.get('addr:housenumber', ''); st = t.get('addr:street')
    if not hn.isdigit() or not st or st not in calles: continue
    if e['type'] == 'node':
        if e['id'] in interp: continue
        p = Point(xy_nodo(N, e['id']))
    elif e['type'] == 'way' and len(e['nodes']) > 2 and all(n in N for n in e['nodes']): p = Polygon([xy_nodo(N, n) for n in e['nodes']]).centroid
    else: continue
    Lc = min(calles[st], key=lambda g: g.distance(p)); s = Lc.project(p)
    a = Lc.interpolate(max(s - 10, 0)); b = Lc.interpolate(min(s + 10, Lc.length))
    qa, qb = a_mapa((a.x, a.y)), a_mapa((b.x, b.y)); dx, dy = qb - qa; ang = math.degrees(math.atan2(dy, dx)) % 180
    if 70 < ang < 110: o = 'V'; crece = qb[1] < qa[1]
    elif ang < 20 or ang > 160: o = 'H'; crece = qb[0] > qa[0]
    else: continue
    q = a_mapa((p.x, p.y))
    h = min(bd['VT'] if o == 'V' else bd['HT'], key=lambda t: abs(t[0] - (q[1] if o == 'V' else q[0])))[1]
    real = int(hn) // 100 * 100; bien = real == h; ok_c += bien; mal_c += not bien
    if not crece: a, b = b, a
    cr = (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x)
    lado = 'izq' if cr > 0 else 'der'; par = int(hn) % 2 == 0
    lados['coincide' if (par and lado == 'der') or (not par and lado == 'izq') else 'no coincide'] += 1
    filas.append((st, hn, h, 'ok' if bien else 'DISTINTA'))
print(f'b) direcciones reales en la centena del mapa: {ok_c} de {ok_c + mal_c}')
for f in filas:
    if f[3] != 'ok': print('   ', f)
print(f"c) lado par/impar: coincide {lados['coincide']} de {sum(lados.values())}")
