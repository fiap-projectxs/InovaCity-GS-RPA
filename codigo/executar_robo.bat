@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo ==== InovaCity: executando o robo de triagem ====
echo.

if exist saida rmdir /s /q saida
mkdir saida
type nul > saida\.gitkeep

echo [1/6] Execucao normal
python main.py --sem-site
if errorlevel 1 goto erro

echo [2/6] Demonstracao: arquivo de entrada ausente
python main.py --entrada nao_existe.csv --saida saida\demo_entrada_ausente
echo [3/6] Demonstracao: servico de notificacao fora do ar
python main.py --saida saida\demo_servico_fora --simular-servico-fora
if errorlevel 1 goto erro

echo [4/6] Segunda execucao (idempotencia)
python main.py --sem-site
if errorlevel 1 goto erro

echo [5/6] Avaliacao do classificador e testes unitarios
python avaliar.py > saida\avaliacao_console.txt 2>&1
python -m unittest tests.test_rpa > saida\testes_unitarios.txt 2>&1

echo [6/6] Gerando o site com estes resultados e abrindo no navegador
set SITE_FONTE=saida
python site\build_site.py
if errorlevel 1 goto erro
start "" "%~dp0site\landing.html"

echo.
echo Pronto. O site mostra os resultados desta execucao.
pause
exit /b 0

:erro
echo.
echo O robo parou com erro. Veja a mensagem acima e saida\execucao.log
pause
exit /b 1
