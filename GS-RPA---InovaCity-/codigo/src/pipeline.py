import csv, json, logging, time
from pathlib import Path
import config as C
from validacao import validar, DadoInvalido
from classificador import Classificador, ler_rotulado
from duplicidade import achar_duplicata
from prioridade import prioridade
from resiliencia import com_retry, ErroServico
from notificador import Notificador
from llm_opcional import resumir

log = logging.getLogger("rpa")

def configurar_log(saida: Path):
    saida.mkdir(parents=True, exist_ok=True)
    for h in list(log.handlers): h.close(); log.removeHandler(h)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    for h in (logging.FileHandler(saida / "execucao.log", mode="a", encoding="utf-8"), logging.StreamHandler()):
        h.setFormatter(fmt); log.addHandler(h)
    log.setLevel(logging.INFO)

def ler_entrada(path: Path):
    """Entrada ausente/ilegivel NAO derruba o robo: retorna None e o relatorio registra."""
    try:
        with open(path, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        log.error("arquivo de entrada ausente: %s", path); return None
    except (UnicodeDecodeError, csv.Error) as e:
        log.error("arquivo de entrada ilegivel: %s", e); return None

def carregar_estado():
    try: return set(json.loads(C.ESTADO.read_text()))
    except (FileNotFoundError, json.JSONDecodeError): return set()

def salvar_csv(path, rows, campos):
    """Acrescenta ao CSV existente (nova execucao nao apaga o historico das filas)."""
    novo = not Path(path).exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        if novo: w.writeheader()
        w.writerows(rows)

def executar(entrada=None, saida=None, notificador_off=False):
    t0 = time.time()
    entrada = Path(entrada or C.ENTRADA); saida = Path(saida or C.SAIDA); C.SAIDA = saida; C.ESTADO = saida / "estado_processados.json"
    configurar_log(saida)
    rel = {"entrada": str(entrada), "status": "ok", "lidas": 0, "invalidas": 0, "ja_processadas": 0, "duplicadas": 0,
           "revisao_humana": 0, "processadas": 0, "notificadas": 0, "notificacao_pendente": 0, "retries_falhos": 0}
    linhas = ler_entrada(entrada)
    if linhas is None:
        rel["status"] = "entrada_ausente_ou_ilegivel"; _fechar(rel, saida, t0, [], [], [], []); return rel
    rel["lidas"] = len(linhas)
    try:
        clf = Classificador().treinar(*ler_rotulado(C.TREINO))
    except Exception as e:                       # sem modelo: tudo vai para revisao humana
        log.error("falha ao treinar classificador: %s", e); clf = None
        rel["status"] = "modelo_indisponivel"
    ja = carregar_estado(); notif = Notificador(saida, C.FALHA_SIMULADA, indisponivel=notificador_off)
    ok, rev, quar, pend, vistos = [], [], [], [], []
    for bruto in linhas:
        iid = bruto.get("id", "?")
        if iid in ja:
            rel["ja_processadas"] += 1; log.info("%s ja processada, ignorada (idempotencia)", iid); continue
        try:
            item = validar(bruto)
        except DadoInvalido as e:
            rel["invalidas"] += 1; quar.append({"id": iid, "motivo": str(e), **{k: bruto.get(k) for k in ("texto","lat","lon","data")}})
            log.warning("%s em quarentena: %s", iid, e); continue
        if clf is None:
            item.update(categoria="", confianca=0.0, motivo="modelo indisponivel"); rev.append(item); continue
        cat, conf = clf.prever(item["texto"]); item.update(categoria=cat, confianca=round(conf, 3))
        if conf < C.LIMIAR_CONFIANCA:
            item["motivo"] = "baixa confianca"; rev.append(item); log.info("%s -> revisao humana (conf %.2f)", iid, conf); ja.add(iid); continue
        dup = achar_duplicata(item, vistos, C.RAIO_DUP_M, C.SIM_DUP)
        if dup:
            rel["duplicadas"] += 1; item["duplicada_de"] = dup; log.info("%s duplicada de %s", iid, dup); ja.add(iid); continue
        item["prioridade"], item["sinais_risco"] = prioridade(cat, item["texto"]); item["sinais_risco"] = ";".join(item["sinais_risco"])
        item["resumo"] = resumir(item["texto"])
        vistos.append(item)
        try:
            item["protocolo"] = com_retry(notif.enviar, {"id": iid, "categoria": cat, "prioridade": item["prioridade"]}, rotulo=iid); rel["notificadas"] += 1
            log.info("%s processada: %s | prioridade %s | confianca %.2f | %s", iid, cat, item["prioridade"], conf, item["protocolo"])
        except (ErroServico, TimeoutError) as e:
            rel["notificacao_pendente"] += 1; item["protocolo"] = ""; pend.append(item); log.error("%s notificacao pendente: %s", iid, e)
        ok.append(item); ja.add(iid)
    rel["retries_falhos"] = notif.falhas; rel["revisao_humana"] = len(rev); rel["processadas"] = len(ok); rel["invalidas"] = len(quar)
    C.ESTADO.write_text(json.dumps(sorted(ja)))
    _fechar(rel, saida, t0, ok, rev, quar, pend); return rel

def _fechar(rel, saida, t0, ok, rev, quar, pend):
    rel["duracao_s"] = round(time.time() - t0, 2)
    salvar_csv(saida / "fila_processadas.csv", sorted(ok, key=lambda x: {"alta":0,"media":1,"baixa":2}[x["prioridade"]]) if ok else [],
               ["id","categoria","confianca","prioridade","sinais_risco","lat","lon","data","texto","resumo","protocolo"])
    salvar_csv(saida / "fila_revisao_humana.csv", rev, ["id","texto","categoria","confianca","motivo","lat","lon","data"])
    qp = saida / "quarentena.csv"
    if qp.exists():
        with open(qp, encoding="utf-8", newline="") as f: ja_q = {(r["id"], r["motivo"]) for r in csv.DictReader(f)}
        quar = [q for q in quar if (q["id"], q["motivo"]) not in ja_q]
    salvar_csv(qp, quar, ["id","motivo","texto","lat","lon","data"])
    salvar_csv(saida / "notificacoes_pendentes.csv", pend, ["id","categoria","prioridade","texto"])
    (saida / "relatorio_execucao.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(saida / "relatorios_historico.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"quando": time.strftime("%Y-%m-%d %H:%M:%S"), **rel}, ensure_ascii=False) + "\n")
    log.info("RELATORIO %s", json.dumps(rel, ensure_ascii=False))
