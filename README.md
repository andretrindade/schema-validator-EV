# Validate-Test

## Objetivo

O script `validate_test.py` tem como objetivo validar os payloads JWT presentes nos logs de testes de APIs, utilizando os schemas definidos em uma especificação OpenAPI. Ele verifica se os dados das requisições e respostas estão em conformidade com o padrão esperado e gera um relatório detalhado dos resultados em formato JSON e CSV.

## Como funciona

- Lê todos os arquivos `.json` de cenários de teste em um diretório especificado.
- Obtém a especificação OpenAPI a partir de uma URL (formato YAML).
- Para cada cenário, valida os payloads JWT das requisições e respostas conforme os schemas definidos na OpenAPI.
- Gera um resumo dos resultados, exibindo no console e salvando em um arquivo CSV.

## Requisitos

- Python 3.11+
- Arquivo `requirements.txt` com as dependências:
  ```
  pandas
  requests
  pyyaml
  jsonschema
  jsonref
  ```

## Instalação

1. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```

2. Certifique-se de ter um diretório chamado `cenarios` com arquivos `.json` de teste.

## Execução

### Via Python

```sh
python validate_test.py https://raw.githubusercontent.com/OpenBanking-Brasil/openapi/main/swagger-apis/credit-portability/1.0.0-rc.1.yml
```

- **cenarios**: diretório contendo os arquivos de teste (.json)
- **URL**: endereço da especificação OpenAPI em formato YAML

### Via Docker

1. Construa a imagem:
   ```sh
   docker build -t validate-test .
   ```

2. Execute o container (montando o diretório de cenários):
   ```sh
    docker run --rm -v "$PWD":/app validate-test "https://raw.githubusercontent.com/OpenBanking-Brasil/openapi/main/swagger-apis/credit-portability/1.0.0-rc.1.yml"
   ```

## Saídas

- Exibe o resultado da validação no console (formato JSON).
- Salva o relatório em `validation_results.csv` para análise posterior.

---

**Observação:**  
O script espera 1 parâmetro obrigatório: URL da especificação
