# Paso 1: extrae del PDF del Mapa Urbano los textos (nombres y alturas) y los
# polígonos rellenos (manzanas). Uso: python 01_extraer_pdf.py MapaUrbano.pdf
# Autor: Matias Millan
import sys, json, pymupdf
p = pymupdf.open(sys.argv[1])[0]
textos = []
for b in p.get_text('dict')['blocks']:
    for l in b.get('lines', []):
        for s in l['spans']:
            t = s['text'].strip()
            if t:
                textos.append({'t': t, 'bbox': [round(x, 1) for x in s['bbox']],
                               'dir': [round(x, 3) for x in l['dir']], 'size': round(s['size'], 1)})
json.dump(textos, open('pdf_textos.json', 'w'), ensure_ascii=False)
rellenos = [{'fill': [round(v, 3) for v in x['fill']], 'items': [[it[0]] + [[pt.x, pt.y] for pt in it[1:] if hasattr(pt, 'x')] for it in x['items']]}
            for x in p.get_drawings() if x.get('fill') and 150 < x['rect'].y0 and x['rect'].y1 < 960]
json.dump(rellenos, open('pdf_rellenos.json', 'w'))
print('textos', len(textos), 'rellenos', len(rellenos))
