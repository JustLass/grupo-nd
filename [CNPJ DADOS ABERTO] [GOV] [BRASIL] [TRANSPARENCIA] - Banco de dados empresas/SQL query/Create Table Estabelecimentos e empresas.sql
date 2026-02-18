create table tb_est_emp_sc_2005_2025 as
select
	left(est.data_inicio_atividade, 4) as ano_abertura,
	est.*,
	emp.razao_social,
	emp.porte_empresa,
	emp.natureza_juridica,
	emp.capital_social
from
	estabelecimentos est
inner join
	empresas emp on emp.cnpj_basico = est.cnpj_basico
where
	est.uf = 'SC'
	and est.data_inicio_atividade between '20050101' and '20251231';