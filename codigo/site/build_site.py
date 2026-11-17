"""Gera site/index.html (arquivo unico, sem dependencias) a partir das saidas REAIS do robo em ../saida."""
import csv, json, re, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent
# SITE_FONTE=saida (usado por executar_robo.bat) mostra a execucao que acabou de rodar; sem isso, usa a execucao congelada dos autores
import os
S = R / "saida" if os.getenv("SITE_FONTE") == "saida" else (R / "evidencias" if (R / "evidencias").exists() else R / "saida")

def csvl(p):
    with open(p, encoding="utf-8", newline="") as f: return list(csv.DictReader(f))

entrada = csvl(R / "dados" / "entrada_ocorrencias.csv")
proc = {r["id"]: r for r in csvl(S / "fila_processadas.csv")}
rev = {r["id"]: r for r in csvl(S / "fila_revisao_humana.csv")}
pend = {r["id"] for r in csvl(S / "notificacoes_pendentes.csv")}

# primeira execucao = linhas do log ate o primeiro RELATORIO
linhas = (S / "execucao.log").read_text(encoding="utf-8").splitlines()
log1 = []
for l in linhas:
    log1.append(l)
    if "RELATORIO" in l: break
rx = re.compile(r"^(\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d),(\d+) (\w+) (.*)$")
def seg(l):
    m = rx.match(l); h, mi, s = m.group(2).split(":"); return int(h)*3600+int(mi)*60+int(s)+int(m.group(3))/1000, m.group(4), m.group(5)
t0 = seg(log1[0])[0]
eventos, tent = [], {}
for l in log1:
    t, nivel, msg = seg(l)
    if msg.startswith("RELATORIO"): continue
    m = re.match(r"(OC\d+) ", msg); iid = m.group(1) if m else None
    if iid and "tentativa" in msg: tent[iid] = tent.get(iid, 0) + 1
    eventos.append({"t": round(t - t0, 2), "n": nivel, "m": msg, "id": iid})

itens = []
for e in entrada:
    iid = e["id"]; it = {"id": iid, "texto": e["texto"], "lat": e["lat"], "lon": e["lon"], "data": e["data"], "tent": tent.get(iid, 0)}
    ev = [x for x in eventos if x["id"] == iid]
    for x in ev:
        m = x["m"]
        if "em quarentena:" in m: it.update(res="quarentena", motivo=m.split("em quarentena: ")[1])
        elif "-> revisao humana" in m:
            it.update(res="revisao", cat=rev[iid]["categoria"], conf=float(rev[iid]["confianca"]), motivo="confiança abaixo de 0,45")
        elif "duplicada de" in m: it.update(res="duplicada", dup=m.split("duplicada de ")[1])
        elif "processada:" in m:
            p = proc[iid]; it.update(res="processada", cat=p["categoria"], conf=float(p["confianca"]), prio=p["prioridade"], sinais=p["sinais_risco"], prot=p["protocolo"])
        elif "notificacao pendente" in m:
            p = proc[iid]; it.update(res="processada", cat=p["categoria"], conf=float(p["confianca"]), prio=p["prioridade"], sinais=p["sinais_risco"], prot="", pendente=True)
    itens.append(it)
assert all("res" in i for i in itens), [i["id"] for i in itens if "res" not in i]
# tempo de cada item = primeiro evento do id
for it in itens:
    it["t"] = next(x["t"] for x in eventos if x["id"] == it["id"])

hist = [json.loads(l) for l in (S / "relatorios_historico.jsonl").read_text(encoding="utf-8").splitlines()]
rel1, rel2 = hist[0], hist[1]
av = json.loads((S / "avaliacao.json").read_text(encoding="utf-8"))

def tail_log(path, n=None, filtro=None):
    ls = [l for l in path.read_text(encoding="utf-8").splitlines()]
    out = []
    for l in ls:
        if "RELATORIO" in l: break
        if filtro is None or filtro(l): out.append(l[11:] if len(l) > 11 else l)
    return out[:n] if n else out
f_ausente = tail_log(S / "demo_entrada_ausente" / "execucao.log")
f_fora = tail_log(S / "demo_servico_fora" / "execucao.log", filtro=lambda l: "tentativa" in l or "pendente" in l)[:7]
f_quar = [x["m"] for x in eventos if "quarentena" in x["m"]]
rel_fora = json.loads((S / "demo_servico_fora" / "relatorio_execucao.json").read_text(encoding="utf-8"))
rel_aus = json.loads((S / "demo_entrada_ausente" / "relatorio_execucao.json").read_text(encoding="utf-8"))
import sys as _s; _s.path.insert(0, str(R / "src"))
import config as _C
from classificador import Classificador, ler_rotulado
_clf = Classificador().treinar(*ler_rotulado(_C.TREINO)); _v, _l = _clf.m.steps[0][1], _clf.m.steps[1][1]
modelo = {"vocab": sorted(_v.vocabulary_, key=_v.vocabulary_.get), "idf": [round(float(x), 6) for x in _v.idf_], "classes": [str(c) for c in _l.classes_],
          "w": [[round(float(x), 6) for x in r] for r in _l.coef_], "b": [round(float(x), 6) for x in _l.intercept_]}
exemplos = [{"nome": n, "csv": (R / "dados" / n).read_text(encoding="utf-8")} for n in ("exemplo_site_1_basico.csv", "exemplo_site_2_dificil.csv")]
data = {"modelo": modelo, "exemplos": exemplos, "itens": itens, "eventos": eventos, "rel1": rel1, "rel2": rel2, "av": av,
        "falhas": {"ausente": f_ausente, "fora": f_fora, "fora_rel": rel_fora, "aus_rel": rel_aus, "quar": f_quar},
        "testes": (S / "testes_unitarios.txt").read_text(encoding="utf-8").strip().splitlines()[-3:]}
tpl = (Path(__file__).parent / "index.template.html").read_text(encoding="utf-8")
import base64
logo = base64.b64encode((Path(__file__).parent / "logo.png").read_bytes()).decode()
bpmn = base64.b64encode((R / "figs" / "bpmn_triagem.png").read_bytes()).decode()
html = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False)).replace("/*__TRIAGEM__*/", (Path(__file__).parent / "triagem.js").read_text(encoding="utf-8")).replace("__LOGO__", logo).replace("__BPMN__", bpmn)
(Path(__file__).parent / "index.html").write_text(html, encoding="utf-8")
print("ok", len(html) // 1024, "KB;", {k: sum(1 for i in itens if i["res"] == k) for k in ("processada","revisao","quarentena","duplicada")})
(Path(__file__).parent / "landing.html").write_text((Path(__file__).parent / "landing.template.html").read_text(encoding="utf-8").replace("__LOGO__", logo), encoding="utf-8")
