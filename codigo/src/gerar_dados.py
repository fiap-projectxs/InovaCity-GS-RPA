"""Gera dados SINTETICOS de ocorrencias urbanas (nenhum dado pessoal real).
Treino e teste usam pools de frases DIFERENTES para o teste nao ser memorizacao."""
import csv, random, sys
from pathlib import Path

CATS = ["buraco_via", "iluminacao", "lixo_entulho", "alagamento_drenagem", "calcada_acessibilidade"]

TREINO = {
 "buraco_via": ["buraco grande na rua", "asfalto quebrado com cratera", "cratera na pista de rolamento", "via esburacada perigosa para carros", "buraco na avenida perto da escola"],
 "iluminacao": ["poste apagado a noite", "lampada queimada na rua", "iluminacao publica falhando", "rua totalmente escura sem luz", "poste piscando e sem energia"],
 "lixo_entulho": ["lixo acumulado na esquina", "entulho jogado na calcada", "sacos de lixo espalhados", "descarte irregular de moveis na rua", "lixo sem coleta ha dias"],
 "alagamento_drenagem": ["bueiro entupido e alagando", "agua empocada apos chuva", "rua alagada quando chove", "galeria de drenagem transbordando", "boca de lobo cheia de folhas"],
 "calcada_acessibilidade": ["calcada quebrada impede cadeirante", "falta rampa de acesso na esquina", "piso tatil danificado", "calcada irregular dificulta idosos", "calcada com degrau alto sem rampa"],
}
TESTE = {
 "buraco_via": ["pista com depressao funda danificando pneus", "pavimento cedeu e abriu um rombo", "motos caem no buraco da via", "tapa-buraco nunca chegou aqui"],
 "iluminacao": ["escuridao na praca por falta de lampada", "luminaria da rua nao acende", "sem luz no poste desde segunda", "trecho escuro, medo de passar a noite"],
 "lixo_entulho": ["restos de obra largados na calcada", "amontoado de lixo atraindo ratos", "caminhao de lixo nao passou esta semana", "colchao e sofa abandonados na via"],
 "alagamento_drenagem": ["agua sobe na rua com qualquer chuva", "bueiro sem tampa e entupido", "enxurrada invade as casas da baixada", "ralo da rua nao escoa a agua"],
 "calcada_acessibilidade": ["passeio com buracos para quem usa muleta", "sem rampa para cadeira de rodas no cruzamento", "calcada estreita e quebrada para idosos", "piso para deficientes visuais arrancado"],
}
URG = ["", "", "", " risco de acidente", " ja houve queda aqui", " crianca quase se machucou", " urgente"]
LOCAIS = ["Rua das Acacias", "Av. Central", "Praca do Bairro", "Rua do Comercio", "Travessa Azul", "Rua da Escola"]
# bairro-piloto ficticio: lat/lon em torno de um ponto
LAT0, LON0 = -23.5600, -46.6500

def ruido(t, r):
    if r.random() < 0.15:
        i = r.randrange(len(t)); t = t[:i] + t[i+1:]       # letra faltando
    if r.random() < 0.1:
        t = t.upper()
    return t

def linha(i, cat, frase, r):
    texto = ruido(f"{frase}{r.choice(URG)} em {r.choice(LOCAIS)}", r)
    return {"id": f"OC{i:04d}", "texto": texto, "lat": round(LAT0 + r.uniform(-.004, .004), 5),
            "lon": round(LON0 + r.uniform(-.004, .004), 5), "data": f"2026-11-{r.randint(1,15):02d}", "rotulo": cat}

def gerar(pool, n, seed, inicio=1):
    r = random.Random(seed); rows = []
    for k in range(n):
        cat = CATS[k % len(CATS)]
        rows.append(linha(inicio + k, cat, r.choice(pool[cat]), r))
    return rows

def salvar(path, rows, campos):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos); w.writeheader()
        for x in rows: w.writerow({c: x[c] for c in campos})

if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "dados"); d.mkdir(exist_ok=True)
    tr = gerar(TREINO, 200, 1)
    te = gerar(TESTE, 100, 2, 1001)
    salvar(d / "treino_rotulado.csv", tr, ["id","texto","lat","lon","data","rotulo"])
    salvar(d / "teste_rotulado.csv", te, ["id","texto","lat","lon","data","rotulo"])
    # lote de entrada do robo: 40 validos (mistura treino/teste) + defeitos + duplicatas + ambiguos
    r = random.Random(3)
    MISTO = {c: TREINO[c] + TESTE[c] for c in CATS}   # frases comuns + frases novas
    ent = gerar(MISTO, 40, 4, 2001)
    # duplicatas: mesmo problema, mesma regiao, texto parecido
    for k in (0, 5, 10):
        b = dict(ent[k]); b["id"] = f"OC{3001+k}"; b["lat"] = round(b["lat"] + .0001, 5); b["texto"] = b["texto"] + " por favor"
        ent.append(b)
    # ambiguos (baixa confianca -> revisao humana)
    for k, t in enumerate(["preciso falar com a prefeitura", "problema aqui", "nao sei explicar, venham ver", "obrigado pelo atendimento"]):
        ent.append({"id": f"OC{3101+k}", "texto": t, "lat": LAT0, "lon": LON0, "data": "2026-11-10", "rotulo": ""})
    # invalidos
    ent.append({"id": "OC3201", "texto": "", "lat": LAT0, "lon": LON0, "data": "2026-11-10", "rotulo": ""})
    ent.append({"id": "OC3202", "texto": "buraco na rua", "lat": "abc", "lon": LON0, "data": "2026-11-10", "rotulo": ""})
    ent.append({"id": "OC3203", "texto": "poste apagado", "lat": 99, "lon": LON0, "data": "2026-11-10", "rotulo": ""})
    ent.append({"id": "OC3204", "texto": "lixo na rua", "lat": LAT0, "lon": LON0, "data": "31/02/2026", "rotulo": ""})
    r.shuffle(ent)
    salvar(d / "entrada_ocorrencias.csv", ent, ["id","texto","lat","lon","data"])
    print("ok", len(tr), len(te), len(ent))
