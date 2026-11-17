"""Duplicidade: mesma categoria + distancia <= RAIO_DUP_M (haversine) + similaridade de texto (Jaccard)."""
from math import radians, sin, cos, asin, sqrt
from classificador import norm

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    a = sin(radians(lat2-lat1)/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(radians(lon2-lon1)/2)**2
    return 2*R*asin(sqrt(a))

def jaccard(a, b):
    A, B = set(norm(a).split()), set(norm(b).split())
    return len(A & B) / len(A | B) if A | B else 0.0

def achar_duplicata(item, vistos, raio, sim):
    for v in vistos:
        if v["categoria"] == item["categoria"] and haversine_m(item["lat"], item["lon"], v["lat"], v["lon"]) <= raio \
           and jaccard(item["texto"], v["texto"]) >= sim:
            return v["id"]
    return None
