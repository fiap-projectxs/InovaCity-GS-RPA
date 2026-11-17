"""NLP: TF-IDF (unigramas+bigramas) + Regressao Logistica. Retorna categoria e confianca."""
import csv, re, unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

def norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", t)

def ler_rotulado(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r["texto"] for r in rows], [r["rotulo"] for r in rows]

class Classificador:
    def __init__(self):
        self.m = make_pipeline(
            TfidfVectorizer(preprocessor=norm, ngram_range=(1, 2), sublinear_tf=True, analyzer="word"),
            LogisticRegression(max_iter=1000, C=10.0))
    def treinar(self, textos, rotulos):
        self.m.fit(textos, rotulos); return self
    def prever(self, texto):
        p = self.m.predict_proba([texto])[0]; i = p.argmax()
        return self.m.classes_[i], float(p[i])
