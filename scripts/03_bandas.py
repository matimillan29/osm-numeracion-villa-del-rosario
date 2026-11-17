# Paso 3: lee las marcas de altura del margen del mapa (0, 100, 200...) y guarda
# su posición: VT para calles norte-sur (por coordenada y del PDF), HT para este-oeste (por x).
# Autor: Matias Millan
import json, re
S = [s for s in json.load(open('pdf_textos.json')) if 150 < s['bbox'][1] < 900 and re.fullmatch(r'\d{1,4}', s['t'])]
VT = sorted([((s['bbox'][1] + s['bbox'][3]) / 2, int(s['t'])) for s in S if abs(s['dir'][1]) > 0.5])
HT = sorted([((s['bbox'][0] + s['bbox'][2]) / 2, int(s['t'])) for s in S if abs(s['dir'][0]) > 0.5])
json.dump({'VT': VT, 'HT': HT}, open('bandas.json', 'w'))
print('marcas VT', len(VT), 'HT', len(HT))
