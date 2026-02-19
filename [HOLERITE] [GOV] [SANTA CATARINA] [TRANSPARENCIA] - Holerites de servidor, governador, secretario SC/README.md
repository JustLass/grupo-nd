# Holerites de Servidores Publicos - Governo de Santa Catarina (2025)

## Contexto

Este projeto nasceu da necessidade de coletar, estruturar e analisar os dados de remuneracao dos servidores publicos do Estado de Santa Catarina, disponibilizados pelo [Portal da Transparencia](https://www.transparencia.sc.gov.br/remuneracao-servidores).

O objetivo era ter uma base completa com os valores de contracheque de todos os servidores ativos ao longo de 2025, cruzados com informacoes de cargo, orgao de exercicio e forma de ingresso.

---

## Fase 1 - Descoberta: inspecionando o site

A primeira abordagem foi automatizar o proprio site via Selenium. Construi uma classe Scraping capaz de navegar pelo portal, selecionar ano e mes, e clicar em **buscar servidores**. O problema e que a paginacao era lenta e o volume de dados tornava essa abordagem inviavel para 12 meses de dados.

Foi entao que abri o **DevTools do Chrome** (F12 -> aba Network) e comecei a inspecionar as requisicoes que o site fazia ao carregar os dados. Descobri que por tras da interface existe uma **API REST propria**:
`
https://api-portal-transparencia.apps.sm.okd4.ciasc.sc.gov.br/api/remuneracao-servidores/analise-detalhada
`
Essa API aceita parametros de mes, page, alem de filtros JSON para tipo de consulta e ordenacao. Muito mais eficiente do que navegar pelo HTML.

---

## Fase 2 - Extracao da base (lista de servidores por mes)

Com a API identificada, construi um pipeline paralelo com ThreadPoolExecutor usando **4 threads simultaneas**, uma por grupo de meses, com:

- Checkpoint a cada 50 paginas para evitar perda de progresso
- Log de progresso por mes (log_mes_XX.txt) permitindo retomada automatica caso a execucao fosse interrompida
- Delay aleatorio entre requisicoes para nao sobrecarregar o servidor
- Retry automatico em caso de erro com pausa de 20 segundos

Cada mes gerou um arquivo transparencia_sc_2025_MM.csv. Ao final, todos foram consolidados em:

\data/details/transparencia_sc_2025_consolidado.csv
\
---

## Fase 3 - Descoberta da API de detalhes (contracheques)

Navegando no portal, percebi que ao clicar em um servidor especifico a pagina carregava um holerite detalhado. Voltei ao DevTools e identifiquei uma segunda API, acessada por um ID numerico unico de cada servidor:

`https://api-portal-transparencia.apps.sm.okd4.ciasc.sc.gov.br/api/remuneracao-servidores-detalhe/{id}
`

Essa API retorna um JSON rico com secoes distintas:

| Secao | Conteudo |
|---|---|
| cargoefetivo | Dados do cargo efetivo (concurso publico) |
| cargocomissionado | Dados do cargo comissionado (se ocupar) |
| contracheque | Valores financeiros: proventos, descontos, liquido, IRRF etc |
| movimentacaocedido | Cedencias a outros orgaos |
| aposentadoria / pensao | Aposentados e pensionistas |

---

## Fase 4 - Modelagem dos dados e o problema das matriculas

A primeira versao do parser era simples: iterar pelos cargos e buscar o contracheque pela matricula. Mas ao testar com casos reais, encontrei dois comportamentos distintos que quebravam a logica:

### Caso 1 - Servidor com dois cargos e matriculas diferentes

Como o servidor AARON: ocupa dois cargos com matriculas distintas, cada um com seu proprio contracheque. Neste caso, cada matricula gera **uma linha separada** com os valores financeiros corretos para aquele vinculo.

### Caso 2 - Servidor com efetivo + comissionado na mesma matricula

Como o servidor ABELARDO: ocupa um cargo efetivo e um comissionado com a **mesma matricula**, com apenas **um contracheque consolidado** para os dois. Processar os cargos de forma linear geraria duplicacao dos valores financeiros.

**Solucao**: agrupar os cargos pela matricula antes de montar as linhas do DataFrame:

- **1 matricula = 1 linha**, com colunas ef_* e com_* lado a lado
- Contracheque linkado uma unica vez pela matricula, sem duplicar valores

Assim, cada linha representa um vinculo (matricula), com:
- ef_* - dados do cargo efetivo
- com_* - dados do cargo comissionado (quando existir, senao fica vazio)
- contra_* - todos os valores financeiros do contracheque

---

## Fase 5 - Extracao em escala dos detalhes

Com a modelagem validada, montei o pipeline final para extrair os detalhes de todos os servidores **ativos** do consolidado. Decisoes tecnicas:

- **Filtro de ativos**: ServidorDescCategoria == ATIVO para excluir aposentados, pensionistas e inativos
- **4 workers em paralelo**, cada um processando 1/4 dos IDs de forma independente
- **Checkpoint a cada 50 registros** por worker, salvando em detalhes_worker_N.csv
- **Retomada automatica**: ao reiniciar, os IDs ja salvos sao lidos e pulados automaticamente
- **Log estruturado por worker** (log_worker_N.txt) com timestamp, checkpoints e erros individuais
- **Pausa aleatoria** de 0.8 a 1.8s entre requisicoes por worker

Saida em:
`
data/details/contracheques/
`


## Estrutura final das colunas

| Coluna | Origem | Descricao |
|---|---|---|
| id_registro | API detalhe | ID unico do registro no portal |
| nome | API detalhe | Nome do servidor |
| ef_matricula | cargoefetivo | Matricula do vinculo efetivo |
| ef_cargo | cargoefetivo | Cargo efetivo ocupado |
| ef_orgao_exercicio | cargoefetivo | Orgao onde exerce |
| ef_forma_ingresso | cargoefetivo | Ex: NOMEACAO POR CONCURSO PUBLICO |
| com_matricula | cargocomissionado | Matricula do comissionado (se houver) |
| com_cargo | cargocomissionado | Cargo comissionado |
| com_orgao_exercicio | cargocomissionado | Orgao de exercicio do comissionado |
| com_forma_ingresso | cargocomissionado | Ex: DESIGNACAO |
| contra_ServidorTotalProventos | contracheque | Total bruto recebido |
| contra_ServidorTotalDesconto | contracheque | Total de descontos |
| contra_ServidorRemuneracaoBasica | contracheque | Remuneracao base |
| contra_ServidorRemuneracaoLiquida | contracheque | Valor liquido recebido |
| contra_ServidorPrevIRRF | contracheque | IRRF + Previdencia |
| contra_ServidorVerbaIndenizatoria | contracheque | Verbas indenizatorias |
| contra_ServidorDecimoTerceiro | contracheque | 13 salario |
| contra_ServidorMesReferencia | contracheque | Mes de referencia |
| contra_ServidorAnoReferencia | contracheque | Ano de referencia |

---

## Tecnologias utilizadas

- **Python 3** com Jupyter Notebook
- requests - requisicoes HTTP as APIs
- pandas - manipulacao e salvamento dos dados
- concurrent.futures.ThreadPoolExecutor - paralelismo das extracoes
- logging - logs estruturados por worker
- selenium - prova de conceito inicial (substituido pela API)