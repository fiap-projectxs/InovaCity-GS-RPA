"""Avalia o classificador no conjunto de teste rotulado (frases diferentes das de treino)."""
import sys, json, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
import config as C
from classificador import Classificador, ler_rotulado

xt, yt = ler_rotulado(C.TREINO); xe, ye = ler_rotulado(C.TESTE)
clf = Classificador().treinar(xt, yt)
pred = [clf.prever(t) for t in xe]
acertos = sum(p[0] == y for p, y in zip(pred, ye))
rev = sum(p[1] < C.LIMIAR_CONFIANCA for p in pred)
auto = [(p, y) for p, y in zip(pred, ye) if p[1] >= C.LIMIAR_CONFIANCA]
ac_auto = sum(p[0] == y for p, y in auto)
conf = collections.Counter((y, p[0]) for p, y in zip(pred, ye) if p[0] != y)
erros = [(i, xe[i], ye[i], pred[i]) for i in range(len(xe)) if pred[i][0] != ye[i]]
res = {"n_treino": len(xt), "n_teste": len(xe), "acuracia_total": round(acertos/len(xe), 3),
       "enviados_a_revisao": rev, "n_automaticos": len(auto), "acuracia_automaticos": round(ac_auto/len(auto), 3) if auto else None,
       "confusoes": {f"{a}->{b}": n for (a, b), n in conf.most_common()}}
print(json.dumps(res, ensure_ascii=False, indent=2))
print("\nERROS (ate 15):")
for i, t, y, p in erros[:15]: print(f"- {t!r}: real={y} previsto={p[0]} conf={p[1]:.2f}")
print("\nLIMIAR x cobertura x acuracia (informativo; limiar usado foi fixado antes: %.2f)" % C.LIMIAR_CONFIANCA)
varre = []
for lim in (0.30, 0.35, 0.40, 0.45, 0.50, 0.60):
    a = [(p, y) for p, y in zip(pred, ye) if p[1] >= lim]
    ac = sum(p[0] == y for p, y in a) / len(a) if a else 0
    varre.append({"limiar": lim, "automaticos": len(a), "acuracia": round(ac, 3)}); print(f"  {lim:.2f}: automaticos={len(a):3d} acuracia={ac:.3f}")
res["varredura_limiar"] = varre
Path(C.RAIZ / "saida").mkdir(exist_ok=True)
(C.RAIZ / "saida" / "avaliacao.json").write_text(json.dumps({**res, "erros": [[t, y, p[0], round(p[1],3)] for _, t, y, p in erros]}, ensure_ascii=False, indent=2), encoding="utf-8")
