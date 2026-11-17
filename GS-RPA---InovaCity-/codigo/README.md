# InovaCity – Robô de triagem de ocorrências (AI for RPA)

**Integrantes:** Rodrigo Wolkoff Giorgi (RM 556980) · Carlos Eduardo Mamede (RM 568269)
**Disciplina:** AI for Robotic Process Automation – FIAP – Global Solution 2026.2 (CitizenTech)

## Problema
Moradores de um bairro-piloto registram problemas de infraestrutura (buraco, poste apagado, lixo, alagamento, calçada sem acessibilidade). Hoje alguém precisa ler cada relato, classificar, descartar duplicatas, decidir a urgência e encaminhar. O robô faz esse fluxo de ponta a ponta e deixa para uma pessoa só o que não consegue resolver com segurança. Sem integração assumida com a prefeitura: o encaminhamento é um serviço **simulado**.

## Fluxo
`CSV de ocorrências → validação → classificação (NLP) → duplicidade → prioridade → notificação (retry) → filas + relatório → site aberto no navegador`

## Como executar (Python 3.10+)
```bash
pip install -r requirements.txt        # só scikit-learn
python src/gerar_dados.py dados        # opcional: regera dados sintéticos (já vêm prontos)
python main.py                         # execução completa; saídas em saida/ e site aberto no navegador
python avaliar.py                      # acurácia no conjunto de teste rotulado
python -m unittest tests.test_rpa      # 9 testes
```
Ao terminar a execução padrão, o robô **regera o site e abre sozinho no navegador** a tela de login (`site/landing.html`); depois de entrar, aparecem os resultados (`site/index.html`). Se o navegador não puder ser aberto, o robô avisa o caminho do arquivo e o processamento não é afetado. Para não abrir o site: `python main.py --sem-site`.

No Windows, dê dois cliques em **`executar_robo.bat`**: ele apaga a `saida/`, roda o robô (execução normal, demonstrações de falha e segunda execução), mede o classificador, roda os testes, gera o site com os resultados dessa execução e abre a tela de login no navegador.

Demonstrações de falha (não abrem o site):
```bash
python main.py --entrada nao_existe.csv --saida saida/demo_entrada_ausente   # arquivo ausente
python main.py --saida saida/demo_servico_fora --simular-servico-fora        # serviço externo fora do ar
python main.py                                                               # 2ª execução: idempotência
```
Em notebook (Colab): `!python main.py --sem-site` na pasta do projeto.

## Quadro de temas
| Tema | Onde entra no fluxo | O que resolve |
|---|---|---|
| Hiperautomação | Orquestração inteira (`src/pipeline.py`): RPA, IA, regras e revisão humana no mesmo fluxo | Decide o que o robô resolve sozinho e o que escala para uma pessoa |
| Processos, tarefas e BPM/BPMN | Processo desenhado em BPMN (`figs/bpmn_triagem.png`) e código dividido em uma tarefa por módulo | Deixa explícito o destino de cada exceção: arquivo ilegível, dado inválido, baixa confiança, duplicidade, serviço fora do ar |
| RPA com arquivos | Leitura do CSV; gravação das filas em CSV, relatório em JSON, log e registro de IDs | Entrada e saída sem digitação; arquivo ausente ou ilegível não derruba a execução |
| RPA com IA: tarefas inteligentes | Classificação NLP (TF-IDF + regressão logística), regras de prioridade e validação, similaridade (Jaccard + haversine) | Categoria, urgência e duplicidade sem leitura humana, com revisão humana quando a confiança é baixa |

## Evidências (pasta `saida/`; cópia da execução dos autores em `evidencias/`)
`relatorio_execucao.json`, `relatorios_historico.jsonl`, `execucao.log`, `fila_processadas.csv` (ordenada por prioridade), `fila_revisao_humana.csv`, `quarentena.csv`, `notificacoes_pendentes.csv`, `avaliacao.json`, `avaliacao_console.txt`, `testes_unitarios.txt`, `demo_*`.

## Proteção de dados, ética e ODS
Todos os dados são sintéticos; nenhum dado pessoal real é usado (o relato não tem nome, telefone ou CPF) e nada é enviado a serviços externos. Decisões de baixa confiança não são automatizadas: vão para revisão humana. Há risco de viés territorial (bairros que mais relatam são priorizados) e de erro de classificação (ver limites no relatório). Contribui com o ODS 9 (infraestrutura resiliente), 11 (cidades sustentáveis) e 10 (inclusão, ao priorizar acessibilidade).

## Site de apresentação
`site/index.html` abre direto no navegador (sem internet) e mostra, a partir das saídas reais do robô: a reprodução da execução relato a relato, as filas, a medição do classificador, as falhas tratadas e o mapa do barema. O robô o regera e o abre automaticamente ao fim de cada `python main.py`.

A seção **Teste com seu arquivo** deixa escolher um CSV (`id,texto,lat,lon,data`) e mostra a triagem com uma interpretação em texto. Há dois exemplos em `dados/`: `exemplo_site_1_basico.csv` (relatos claros) e `exemplo_site_2_dificil.csv` (duplicata, textos vagos, vocabulário novo e linhas inválidas). Essa seção roda no navegador uma versão em JavaScript da lógica do robô (`site/triagem.js`, com o modelo exportado do Python); o arquivo não sai do computador e não há notificação ao serviço externo. O robô completo continua sendo `python main.py`.

Para regerar o site sem rodar o robô: `python site/build_site.py`.

## Estrutura
`main.py` (entrada) · `figs/` (BPMN) · `avaliar.py` · `src/` (config, validacao, classificador, duplicidade, prioridade, resiliencia, notificador, pipeline, gerar_dados) · `dados/` · `site/` · `tests/` · `saida/`
