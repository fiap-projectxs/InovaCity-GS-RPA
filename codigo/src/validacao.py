"""Validacao de linhas. Linha invalida vai para quarentena com o motivo, sem parar o robo."""
from datetime import date

class DadoInvalido(ValueError):
    pass

def validar(l: dict) -> dict:
    texto = (l.get("texto") or "").strip()
    if len(texto) < 3:
        raise DadoInvalido("texto vazio ou curto")
    try:
        lat, lon = float(l["lat"]), float(l["lon"])
    except (TypeError, ValueError, KeyError):
        raise DadoInvalido("coordenada nao numerica")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise DadoInvalido("coordenada fora do intervalo")
    try:
        a, m, d = (int(x) for x in str(l.get("data", "")).split("-"))
        dt = date(a, m, d)
    except (ValueError, TypeError):
        raise DadoInvalido("data invalida (esperado AAAA-MM-DD)")
    return {"id": str(l["id"]), "texto": texto, "lat": lat, "lon": lon, "data": dt.isoformat()}
