# Utilidades comunes: proyección local en metros y carga de datos de OSM.
# Autor: Matias Millan
import json, math
import numpy as np

LAT0 = -31.555
LON0 = -63.54
KX = 111320 * math.cos(math.radians(LAT0))
KY = 110574
BBOX = (-63.565, -31.575, -63.515, -31.535)  # oeste, sur, este, norte

def a_xy(lon, lat):
    return ((lon - LON0) * KX, (lat - LAT0) * KY)

def a_lonlat(p):
    return [round(p[0] / KX + LON0, 7), round(p[1] / KY + LAT0, 7)]

def cargar_osm(ruta):
    d = json.load(open(ruta))['elements']
    N = {e['id']: e for e in d if e['type'] == 'node'}
    W = {e['id']: e for e in d if e['type'] == 'way'}
    return d, N, W

def xy_nodo(N, n):
    return a_xy(N[n]['lon'], N[n]['lat'])

def transformacion(ruta='afin.json'):
    """Devuelve (mapa->metros, metros->mapa) a partir de las imágenes de (0,0),(1,0),(0,1)."""
    B = np.array(json.load(open(ruta)))
    o = B[0]; M = np.column_stack([B[1] - o, B[2] - o]); Mi = np.linalg.inv(M)
    return (lambda q: M @ np.array(q) + o), (lambda p: Mi @ (np.array(p) - o))
