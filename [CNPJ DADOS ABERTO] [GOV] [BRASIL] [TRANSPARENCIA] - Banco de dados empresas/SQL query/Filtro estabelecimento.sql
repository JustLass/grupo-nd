
/*
Período: Janeiro de 2005 a Dezembro de 2025 (projeção/dados atuais).
Recorte Geográfico: Filtrar apenas estabelecimentos localizados em Santa Catarina (Tabela ESTABELECIMENTOS, campo UF = "SC").
Status: Considerar empresas ativas e baixadas para análise de ciclo de vida (Tabela ESTABELECIMENTOS, campo SITUAÇÃO CADASTRAL). 
*/

select 
*
from 
	estabelecimentos
where 
	uf = 'SC'
	and data_inicio_atividade between '20050101' and '20251231'
	and trim(situacao_cadastral) = '02'
