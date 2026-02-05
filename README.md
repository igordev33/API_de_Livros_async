# API de Livros

API RESTful para gerenciamento de livros desenvolvida com FastAPI, SQLAlchemy, Redis e SQLite.

## Tecnologias Utilizadas

- **Python 3.11**
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para manipulação do banco de dados
- **SQLite** - Banco de dados relacional
- **Redis** - Sistema de cache em memória
- **Docker & Docker Compose** - Containerização da aplicação
- **Pydantic** - Validação de dados

## Funcionalidades

- Autenticação HTTP Basic
- CRUD completo de livros
- Sistema de cache com Redis
- Paginação de resultados
- Endpoints de debug e health check

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
DATABASE_URL=sqlite:///./database.db
API_USER=seu_usuario
API_PASSWORD=sua_senha
```

### Dependências

As dependências estão listadas no arquivo `requirements.txt`:

- fastapi==0.115.5
- uvicorn[standard]==0.32.1
- sqlalchemy==2.0.36
- redis==5.2.0

## Como Executar

### Com Docker Compose

```bash
docker-compose up --build
```

A API estará disponível em `http://localhost:8000`

### Documentação Interativa

Após executar a aplicação, acesse:

- Swagger UI: `http://localhost:8000/docs`

## Endpoints da API

### Health Check

```
GET /healthy
```

Verifica se a API está funcionando.

**Resposta:**
```json
{
  "message": "Healthy"
}
```

### Listar Livros

```
GET /livros?page=1&limit=10
```

Lista livros com paginação e cache Redis.

**Parâmetros de Query:**
- `page` (int, padrão: 1) - Número da página
- `limit` (int, padrão: 10) - Quantidade de itens por página

**Autenticação:** Requerida (HTTP Basic)

**Resposta:**
```json
{
  "page": 1,
  "limit": 10,
  "total": 50,
  "livros": [
    {
      "id": 1,
      "nome_livro": "1984",
      "autor_livro": "George Orwell",
      "ano_livro": 1949
    }
  ]
}
```

### Criar Livro

```
POST /livros
```

Cadastra um novo livro no sistema.

**Autenticação:** Requerida (HTTP Basic)

**Body:**
```json
{
  "nome_livro": "1984",
  "autor_livro": "George Orwell",
  "ano_livro": 1949
}
```

**Resposta:**
```json
{
  "message": "Livro cadastrado com sucesso"
}
```

### Atualizar Livro

```
PUT /livros/{id}
```

Atualiza os dados de um livro existente.

**Autenticação:** Requerida (HTTP Basic)

**Parâmetros de Path:**
- `id` (int) - ID do livro

**Body:**
```json
{
  "nome_livro": "1984",
  "autor_livro": "George Orwell",
  "ano_livro": 1949
}
```

**Resposta:**
```json
{
  "message": "Livro atualizado com sucesso"
}
```

### Deletar Livro

```
DELETE /livros/{id}
```

Remove um livro do sistema.

**Autenticação:** Requerida (HTTP Basic)

**Parâmetros de Path:**
- `id` (int) - ID do livro

**Resposta:**
```json
{
  "message": "Livro deletado com sucesso"
}
```

### Debug Redis

```
GET /debug/redis
```

Lista todas as chaves armazenadas no Redis com seus valores e TTL.

**Autenticação:** Requerida (HTTP Basic)

**Resposta:**
```json
[
  {
    "key": "livros:page=1:limit=10",
    "ttl": 45,
    "valor": { ... }
  }
]
```

## Autenticação

Todos os endpoints (exceto `/healthy`) requerem autenticação HTTP Basic usando as credenciais configuradas nas variáveis de ambiente `API_USER` e `API_PASSWORD`.

## Sistema de Cache

A API utiliza Redis para cache de consultas de listagem de livros com TTL de 60 segundos. O cache é invalidado automaticamente quando há operações de criação, atualização ou exclusão de livros.

## Modelo de Dados

### Livro (LivroDB)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | Integer | Chave primária (autoincremento) |
| nome_livro | String | Nome do livro (obrigatório) |
| autor_livro | String | Autor do livro (obrigatório) |
| ano_livro | Integer | Ano de publicação (obrigatório) |
