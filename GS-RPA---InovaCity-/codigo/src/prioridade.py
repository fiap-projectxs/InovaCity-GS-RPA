"""Regras de prioridade (transparentes e auditaveis)."""
RISCO = ("risco", "acidente", "queda", "caiu", "crianca", "urgente", "perigo", "perigosa", "medo", "invade", "cadeira", "idosos", "muleta")
BASE = {"buraco_via": 2, "iluminacao": 2, "alagamento_drenagem": 3, "lixo_entulho": 1, "calcada_acessibilidade": 2}

def prioridade(categoria, texto):
    from classificador import norm
    t = norm(texto); pts = BASE.get(categoria, 1)
    hits = [w for w in RISCO if w in t]
    pts += min(2, len(hits))
    nivel = "alta" if pts >= 4 else "media" if pts >= 3 else "baixa"
    return nivel, hits
