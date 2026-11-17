"""Configuracao. Chaves SO por variavel de ambiente (nunca no codigo/repositorio)."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = Path(os.getenv("RPA_ENTRADA", RAIZ / "dados" / "entrada_ocorrencias.csv"))
TREINO = RAIZ / "dados" / "treino_rotulado.csv"
TESTE = RAIZ / "dados" / "teste_rotulado.csv"
SAIDA = Path(os.getenv("RPA_SAIDA", RAIZ / "saida"))
ESTADO = SAIDA / "estado_processados.json"        # idempotencia
LIMIAR_CONFIANCA = float(os.getenv("RPA_LIMIAR", "0.45"))   # abaixo -> revisao humana
RAIO_DUP_M = 150.0
SIM_DUP = 0.6
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").lower()   # "", "openai", "google": opcional
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
FALHA_SIMULADA = float(os.getenv("RPA_FALHA_NOTIFICADOR", "0.3"))  # prob. de erro do servico externo simulado
