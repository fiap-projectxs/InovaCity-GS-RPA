"""Retry com espera exponencial e timeout; erro final vira resultado seguro, nao excecao."""
import logging, time
log = logging.getLogger("rpa")

class ErroServico(Exception):
    pass

def com_retry(fn, *args, tentativas=3, espera=0.2, rotulo="", **kw):
    for t in range(1, tentativas + 1):
        try:
            return fn(*args, **kw)
        except (ErroServico, TimeoutError) as e:
            log.warning("%s tentativa %d/%d falhou: %s", rotulo, t, tentativas, e)
            if t == tentativas:
                raise
            time.sleep(espera * 2 ** (t - 1))
