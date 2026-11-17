#!/bin/sh
# Descarga los datos actuales de OSM del casco urbano de Villa del Rosario.
# Autor: Matias Millan
curl -s -A "numeracion-vdr" "https://api.openstreetmap.org/api/0.6/map.json?bbox=-63.565,-31.575,-63.515,-31.535" -o osm.json
