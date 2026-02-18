import os
import pandas as pd
from sqlalchemy import create_engine, text

PASTA_RAIZ = './Tabelas extraidas'
SENHA_DB = "2560"

STRING_CONEXAO = f"postgresql://postgres:{SENHA_DB}@localhost:5432/cnpj_receita"

CONFIG_IMPORTACAO = {
    "Empresas": {
        "tabela_sql": "empresas",
        # Fonte: PDF Página 1 [cite: 2]
        "colunas": [
            "cnpj_basico", "razao_social", "natureza_juridica", "qualificacao_responsavel",
            "capital_social", "porte_empresa", "ente_federativo_responsavel"
        ]
    },
    "Estabelecimentos": {
        "tabela_sql": "estabelecimentos",
        # Fonte: PDF Páginas 1, 2 e 3 [cite: 3, 5-15, 17, 19]
        "colunas": [
            "cnpj_basico", "cnpj_ordem", "cnpj_dv", "identificador_matriz_filial", 
            "nome_fantasia", "situacao_cadastral", "data_situacao_cadastral", 
            "motivo_situacao_cadastral", "nome_cidade_exterior", "pais", 
            "data_inicio_atividade", "cnae_fiscal_principal", "cnae_fiscal_secundaria", 
            "tipo_logradouro", "logradouro", "numero", "complemento", "bairro", "cep", 
            "uf", "municipio", "ddd_1", "telefone_1", "ddd_2", "telefone_2", 
            "ddd_fax", "fax", "correio_eletronico", "situacao_especial", "data_situacao_especial"
        ]
    },
    "Socios": {
        "tabela_sql": "socios",
        # Fonte: PDF Página 4 
        "colunas": [
            "cnpj_basico", "identificador_socio", "nome_socio_razao_social", 
            "cnpj_cpf_socio", "qualificacao_socio", "data_entrada_sociedade", 
            "pais", "representante_legal", "nome_do_representante", 
            "qualificacao_representante", "faixa_etaria"
        ]
    },
    "Simples": {
        "tabela_sql": "simples",
        # Fonte: PDF Página 3 [cite: 20]
        "colunas": [
            "cnpj_basico", "opcao_pelo_simples", "data_opcao_simples", 
            "data_exclusao_simples", "opcao_pelo_mei", "data_opcao_mei", 
            "data_exclusao_mei"
        ]
    },
    
    "Cnaes": {
        "tabela_sql": "cnaes",
        "colunas": ["codigo", "descricao"] # [cite: 36]
    },
    "Motivos": {
        "tabela_sql": "motivos",
        "colunas": ["codigo", "descricao"] # Padrão Receita
    },
    "Municipios": {
        "tabela_sql": "municipios",
        "colunas": ["codigo", "descricao"] # [cite: 33]
    },
    "Naturezas": {
        "tabela_sql": "naturezas",
        "colunas": ["codigo", "descricao"] # [cite: 35]
    },
    "Paises": {
        "tabela_sql": "paises",
        "colunas": ["codigo", "descricao"] # [cite: 26, 27]
    },
    "Qualificacoes": {
        "tabela_sql": "qualificacoes",
        "colunas": ["codigo", "descricao"] # [cite: 34]
    }
}

def processar_banco():
    engine = create_engine(STRING_CONEXAO)
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print('Conexão com o banco "cnpj_receita" OK!')
    except Exception as e:
        print(f'Erro de conexão: {e}')
        return
    
    for pasta_categoria, config in CONFIG_IMPORTACAO.items():
        
        caminho_pasta = os.path.join(PASTA_RAIZ, pasta_categoria)
        
        if not os.path.exists(caminho_pasta):
            print(f'Pasta "{pasta_categoria}" Não encontrada em "{caminho_pasta}" pulando..')
            continue
        
        arquivos = [f for f in os.listdir(caminho_pasta) if not f.startswith('.')]
        print(f'\n Processando: {pasta_categoria} -> Tabela SQL: "{config['tabela_sql']}"')
        
        for arquivo in arquivos:
            arquivo_path = os.path.join(caminho_pasta, arquivo)
            print(f'    Lendo: {arquivo}...', end="")
            
            try:
                chunks = pd.read_csv(
                    arquivo_path,
                    sep=';',
                    encoding='latin1',
                    header=None,
                    names=config['colunas'],
                    dtype=str,
                    chunksize=200000,
                    quotechar='"'
                )
                
                for chunk in chunks:
                    
                    if pasta_categoria == 'Empresas' and 'capital_social' in chunk.columns:
                        chunk['capital_social'] = chunk['capital_social'].str.replace(',','.', regex=False)
                        chunk['capital_social'] = pd.to_numeric(chunk['capital_social'], errors='coerce')
                        
                    chunk.to_sql(
                        config['tabela_sql'],
                        engine,
                        if_exists="append",
                        index=False,
                        method='multi',
                        chunksize=10000
                    )
                print('Ok')
            except Exception as e:
                print(f'Erro {e}')
                
    print(f'\n Processo finalizado')
    
if __name__ == "__main__":
    processar_banco()