"""Ponto de entrada: python main.py [--entrada caminho.csv] [--saida pasta] [--sem-site]

Ao terminar a execucao padrao, o robo regera o site com as saidas e abre a tela de login (site/landing.html); apos entrar, o navegador mostra os resultados.
"""
import argparse, subprocess, sys, webbrowser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from pipeline import executar

RAIZ = Path(__file__).resolve().parent


def abrir_site():
    """Regera o site a partir das saidas e abre no navegador. Falha aqui nunca derruba o robo."""
    try:
        subprocess.run([sys.executable, str(RAIZ / "site" / "build_site.py")], check=True, cwd=RAIZ, capture_output=True)
        pagina = RAIZ / "site" / "landing.html"   # abre na tela de login; depois do login vai para os resultados (index.html)
        if webbrowser.open(pagina.as_uri()):
            print(f"Site aberto no navegador: {pagina}")
        else:
            print(f"Nao consegui abrir o navegador. Abra manualmente: {pagina}")
    except Exception as e:  # noqa: BLE001
        print(f"Aviso: site nao foi aberto ({e}). O processamento do robo nao foi afetado.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Robo InovaCity: triagem automatica de ocorrencias urbanas")
    ap.add_argument("--entrada"); ap.add_argument("--saida")
    ap.add_argument("--simular-servico-fora", action="store_true", help="demonstra falha do servico de notificacao")
    ap.add_argument("--sem-site", action="store_true", help="nao abre o site ao terminar")
    a = ap.parse_args()
    r = executar(a.entrada, a.saida, a.simular_servico_fora)
    print(r)
    # execucoes de demonstracao (saida/entrada customizadas) nao abrem o site, que mostra a execucao padrao
    if not a.sem_site and not a.saida and not a.entrada:
        abrir_site()
