# Numeración de calles de Villa del Rosario (Córdoba) para OpenStreetMap

Scripts y datos de la propuesta de importación de la numeración de calles (alturas) de Villa del Rosario, Córdoba, Argentina, a partir del Mapa Urbano de Coovilros.

- Plan de importación: https://wiki.openstreetmap.org/wiki/Import/Villa_del_Rosario_numeraci%C3%B3n_Coovilros
- Discusión: https://community.openstreetmap.org/t/150241

## Datos para revisar

| Archivo | Contenido |
|---|---|
| `datos/lineas_numeracion.geojson` | Líneas propuestas, para ver en geojson.io, uMap o QGIS |
| `datos/numeracion_villa_del_rosario.osm` | Las mismas líneas en esquema OSM, para abrir en JOSM (no se puede subir desde el archivo: `upload='never'`) |
| `datos/afin.json` | Georreferenciación del mapa calculada en el paso 2 |
| `datos/bandas.json` | Posición de las marcas de altura del mapa (paso 3) |

Los datos se regeneran contra OSM actual inmediatamente antes de cada subida, así que la versión subida puede diferir levemente de esta.

## Etiquetas

| Elemento | Etiqueta | Valor |
|---|---|---|
| Vía | `addr:interpolation` | `even` (pares) u `odd` (impares) |
| Vía | `addr:street` | nombre de la calle tal como está en OSM |
| Nodo inicial y final | `addr:housenumber` | altura del extremo |
| Nodo inicial y final | `addr:street` | nombre de la calle tal como está en OSM |
| Changeset | `source` | `Coovilros Mapa Urbano 2026` |
| Changeset | `import` | `yes` |

## Fuente

Mapa Urbano de Villa del Rosario, Coovilros Ltda., edición 2026: https://www.coovilros.com/Descargas/MapaUrbano.pdf (no se incluye en el repositorio). El mapa es esquemático: no se copia su geometría, solo los rangos de alturas por cuadra y la ubicación de las manzanas.

## Cómo se reproduce

Requiere Python 3 con `pymupdf`, `shapely` y `numpy` (por ejemplo con `uv run --with pymupdf --with shapely --with numpy python ...`). Desde `scripts/`:

1. `./descargar_osm.sh` — baja los datos actuales de OSM del casco urbano (`osm.json`).
2. `python 01_extraer_pdf.py MapaUrbano.pdf` — extrae textos y manzanas del PDF.
3. `python 02_georreferenciar.py` — ajusta una semejanza entre los nombres de calles del mapa y las calles de OSM (refinada por ICP).
4. `python 03_bandas.py` — lee las marcas de altura del margen del mapa.
5. `python 04_generar.py` — genera una línea por cuadra y por lado, a 6 m de la calle de OSM: pares a la derecha en el sentido en que crecen las alturas. Omite cuadras sin manzana de ese lado, canteros centrales, tramos que ya tienen numeración en OSM, calles en diagonal y las zonas excluidas.
6. `python 05_control.py` — controles: cruces con calles y comparación contra direcciones ya cargadas en OSM.
7. `python 06_exportar.py` — exporta GeoJSON y .osm.

## Resultado de los controles (16/11/2026)

- 1013 líneas en 112 calles; ninguna toca o cruza una calle.
- Direcciones reales ya cargadas en OSM: 28 de 31 caen en la centena que da el mapa; el lado par/impar coincide en 24 de 31.

## Licencia

Scripts: MIT. Datos derivados: ODbL, con autorización de Coovilros para su uso en OpenStreetMap.

Autor: Matias Millan (matimillan en OpenStreetMap).
