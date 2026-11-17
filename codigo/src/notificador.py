"""Servico externo SIMULADO (substitui e-mail/API da prefeitura, que nao assumimos existir).
Falha aleatoriamente (semente fixa) para demonstrar retry. Grava 'protocolo' em arquivo local."""
import random, json
from resiliencia import ErroServico

class Notificador:
    def __init__(self, pasta, prob_falha, semente=7, indisponivel=False):
        self.pasta = pasta; self.p = prob_falha; self.r = random.Random(semente); self.off = indisponivel
        self.enviados = []; self.falhas = 0
    def enviar(self, protocolo: dict):
        if self.off or self.r.random() < self.p:
            self.falhas += 1
            raise ErroServico("servico de notificacao indisponivel")
        self.enviados.append(protocolo)
        return f"PROT-{protocolo['id']}"
