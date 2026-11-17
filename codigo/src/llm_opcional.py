"""LLM OPCIONAL: resume a ocorrencia em uma frase para o painel. Sem chave/falha/resposta vazia -> texto original.
Nao envia coordenadas nem dados pessoais; so o texto sintetico da ocorrencia."""
import logging
from config import LLM_PROVIDER, LLM_API_KEY
log = logging.getLogger("rpa")

def resumir(texto: str) -> str:
    if not (LLM_PROVIDER and LLM_API_KEY):
        return texto
    try:
        raise NotImplementedError("ligue aqui o cliente do provedor escolhido")  # ponto de extensao
    except Exception as e:
        log.warning("LLM indisponivel (%s); usando texto original", e)
        return texto
