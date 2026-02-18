create table tb_mei_emp_sc_2005_2025 as
	select
		left(est.data_inicio_atividade, 4) as ano_abertura,
		est.data_inicio_atividade as est_inicio_atividade,
		est.uf,
		sim.*
	from
		estabelecimentos est
	inner join
		simples sim on est.cnpj_basico = sim.cnpj_basico 
	where
		est.uf = 'SC'
		and est.data_inicio_atividade between '20050101' and '20251231'
		and sim.opcao_pelo_mei = 'S';