import sys, tempfile, json, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from validacao import validar, DadoInvalido
from duplicidade import haversine_m, jaccard
from resiliencia import com_retry, ErroServico
from prioridade import prioridade
import pipeline, config as C

class T(unittest.TestCase):
    def test_valida_ok(self):
        self.assertEqual(validar({"id": "1", "texto": "buraco", "lat": "-23.5", "lon": "-46.6", "data": "2026-11-01"})["data"], "2026-11-01")
    def test_invalidos(self):
        base = {"id": "1", "texto": "buraco", "lat": 1, "lon": 1, "data": "2026-11-01"}
        for k, v in (("texto", ""), ("lat", "x"), ("lat", 100), ("data", "31/02/2026")):
            with self.assertRaises(DadoInvalido): validar({**base, k: v})
    def test_haversine(self):
        self.assertAlmostEqual(haversine_m(0, 0, 0, 0), 0); self.assertTrue(100 < haversine_m(0, 0, 0, .001) < 120)
    def test_jaccard(self):
        self.assertEqual(jaccard("a b", "a b"), 1.0); self.assertEqual(jaccard("a", "b"), 0.0)
    def test_retry_sucesso_e_falha(self):
        n = {"c": 0}
        def f():
            n["c"] += 1
            if n["c"] < 3: raise ErroServico("x")
            return "ok"
        self.assertEqual(com_retry(f, espera=0), "ok")
        def g(): raise ErroServico("x")
        with self.assertRaises(ErroServico): com_retry(g, tentativas=2, espera=0)
    def test_prioridade(self):
        self.assertEqual(prioridade("alagamento_drenagem", "invade as casas risco")[0], "alta")
        self.assertEqual(prioridade("lixo_entulho", "lixo na esquina")[0], "baixa")
    def test_entrada_ausente_nao_quebra(self):
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.executar(Path(d) / "nao_existe.csv", Path(d) / "s")
            self.assertEqual(r["status"], "entrada_ausente_ou_ilegivel")
    def test_idempotencia_e_quarentena(self):
        with tempfile.TemporaryDirectory() as d:
            r1 = pipeline.executar(None, Path(d)); r2 = pipeline.executar(None, Path(d))
            self.assertEqual(r1["invalidas"], 4); self.assertGreater(r1["processadas"], 0)
            self.assertEqual(r2["processadas"], 0); self.assertEqual(r2["ja_processadas"], r1["lidas"] - 4)
    def test_servico_fora_vai_para_pendentes(self):
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.executar(None, Path(d), notificador_off=True)
            self.assertEqual(r["notificadas"], 0); self.assertEqual(r["notificacao_pendente"], r["processadas"])

if __name__ == "__main__": unittest.main()
