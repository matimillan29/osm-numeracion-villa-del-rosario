# Paso 6: exporta las líneas al esquema de OSM.
#  - lineas_numeracion.geojson: para revisar en cualquier SIG o en umap/geojson.io
#  - numeracion_villa_del_rosario.osm: para abrir en JOSM (ids negativos, upload='never')
# Etiquetas: vía solo addr:interpolation=even|odd (la vía no lleva addr:street,
# ver wiki Addresses); nodos extremos addr:housenumber + addr:street.
# Autor: Matias Millan
import json
from xml.sax.saxutils import quoteattr
L = json.load(open('lineas.json'))
feats = [{'type': 'Feature', 'properties': {'addr:interpolation': l['parity'], 'calle': l['street'], 'desde': l['from'], 'hasta': l['to']},
          'geometry': {'type': 'LineString', 'coordinates': l['coords']}} for l in L]
json.dump({'type': 'FeatureCollection', 'features': feats}, open('lineas_numeracion.geojson', 'w'), ensure_ascii=False)
nid = 0; wid = 0; nodos = []; vias = []
for l in L:
    refs = []
    for i, (lon, lat) in enumerate(l['coords']):
        nid -= 1; tags = {}
        if i == 0: tags = {'addr:housenumber': str(l['from']), 'addr:street': l['street']}
        elif i == len(l['coords']) - 1: tags = {'addr:housenumber': str(l['to']), 'addr:street': l['street']}
        nodos.append((nid, lon, lat, tags)); refs.append(nid)
    wid -= 1; vias.append((wid, refs, {'addr:interpolation': l['parity']}))
with open('numeracion_villa_del_rosario.osm', 'w', encoding='utf-8') as f:
    f.write("<?xml version='1.0' encoding='UTF-8'?>\n<osm version='0.6' upload='never' generator='numeracion-vdr'>\n")
    for i, lon, lat, tags in nodos:
        if tags:
            f.write(f"  <node id='{i}' lat='{lat}' lon='{lon}'>\n" + ''.join(f"    <tag k={quoteattr(k)} v={quoteattr(v)} />\n" for k, v in tags.items()) + "  </node>\n")
        else:
            f.write(f"  <node id='{i}' lat='{lat}' lon='{lon}' />\n")
    for i, refs, tags in vias:
        f.write(f"  <way id='{i}'>\n" + ''.join(f"    <nd ref='{r}' />\n" for r in refs) + ''.join(f"    <tag k={quoteattr(k)} v={quoteattr(v)} />\n" for k, v in tags.items()) + "  </way>\n")
    f.write('</osm>\n')
print('exportadas', len(feats), 'líneas,', len(nodos), 'nodos')
