# API de Livros

API RESTful para gerenciamento de livros desenvolvida com FastAPI, SQLAlchemy, Redis, SQLite e Celery.

## Tecnologias Utilizadas

- **Python 3.11**
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para manipulação do banco de dados
- **SQLite** - Banco de dados relacional
- **Redis** - Sistema de cache em memória e broker de mensagens
- **Celery** - Sistema de filas para processamento assíncrono de tarefas
- **Docker & Docker Compose** - Containerização da aplicação
- **Pydantic** - Validação de dados

## Funcionalidades

- Autenticação HTTP Basic
- CRUD completo de livros
- Sistema de cache com Redis
- Paginação de resultados
- Processamento assíncrono de tarefas com Celery
- Endpoints de debug e health check

## Arquitetura

```
FastAPI (app) → publica task → Redis (broker) → Celery Worker consome e executa
```

O Redis atua com duas responsabilidades:
- **Cache** — armazena resultados de consultas de livros com TTL de 60 segundos
- **Broker** — fila de mensagens entre o FastAPI e o Celery Worker

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

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
sqlalchemy==2.0.36
redis==5.2.0
celery==5.6.2
```

## Como Executar

### Com Docker Compose (recomendado)

Sobe todos os serviços juntos (API, Redis e Celery Worker):

```bash
docker-compose up --build
```

Os seguintes serviços estarão disponíveis:
- **API** → `http://localhost:8000`
- **Redis** → `localhost:6379`
- **Celery Worker** → rodando em background, sem porta exposta

Para acompanhar os logs do worker em tempo real:

```bash
docker-compose logs -f celery_worker
```

### Sem Docker (ambiente local)

**1. Instale as dependências:**
```bash
pip install -r requirements.txt
```

**2. Suba o Redis localmente (necessário ter o Docker):**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**3. Em um terminal, inicie a API:**
```bash
uvicorn main:app --reload
```

**4. Em outro terminal, inicie o Celery Worker:**
```bash
celery -A celery_app worker --loglevel=info
```

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

---

### Listar Livros

```
GET /livros?page=1&limit=10
```

Lista livros com paginação e cache Redis.

**Autenticação:** Requerida (HTTP Basic)

**Parâmetros de Query:**
- `page` (int, padrão: 1) - Número da página
- `limit` (int, padrão: 10) - Quantidade de itens por página

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

---

### Criar Livro

```
POST /livros
```

Cadastra um novo livro. Invalida o cache do Redis automaticamente.

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

---

### Atualizar Livro

```
PUT /livros/{id}
```

Atualiza os dados de um livro existente. Invalida o cache do Redis automaticamente.

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

---

### Deletar Livro

```
DELETE /livros/{id}
```

Remove um livro do sistema. Invalida o cache do Redis automaticamente.

**Autenticação:** Requerida (HTTP Basic)

**Parâmetros de Path:**
- `id` (int) - ID do livro

**Resposta:**
```json
{
  "message": "Livro deletado com sucesso"
}
```

---

### Calcular Soma (assíncrono)

```
POST /calcular/soma?a=1&b=2
```

Envia uma task de soma para o Celery Worker processar de forma assíncrona.

**Parâmetros de Query:**
- `a` (int) - Primeiro número
- `b` (int) - Segundo número

**Resposta:**
```json
{
  "task_id": "d2918a6f-4963-4f13-a02a-62ca6cbcdfe4",
  "status": "PENDING",
  "message": "Tarefa de calcular soma disparada com sucesso"
}
```

> Guarde o `task_id` para consultar o resultado posteriormente.

---

### Calcular Fatorial (assíncrono)

```
POST /calcular/fatorial?n=5
```

Envia uma task de fatorial para o Celery Worker processar de forma assíncrona.

**Parâmetros de Query:**
- `n` (int) - Número para calcular o fatorial

**Resposta:**
```json
{
  "task_id": "a1b2c3d4-...",
  "status": "PENDING",
  "message": "Tarefa de calcular fatorial disparada com sucesso"
}
```

---

### Listar Fila do Celery

```
GET /fila_celery
```

Lista as tasks ativas, reservadas e agendadas no Celery Worker.

**Resposta:**
```json
{
  "ativas": {
    "celery@worker": [
      {
        "id": "d2918a6f-...",
        "name": "celery_app.calcular_soma",
        "args": [1, 2]
      }
    ]
  },
  "reservadas": {},
  "agendadas": {}
}
```

---

### Debug Redis

```
GET /debug/redis
```

Lista todas as chaves de cache armazenadas no Redis com seus valores e TTL.

**Autenticação:** Requerida (HTTP Basic)

**Resposta:**
```json
[
  {
    "key": "livros:page=1:limit=10",
    "ttl": 45,
    "valor": { "..." : "..." }
  }
]
```

---

## Testando os Endpoints Assíncronos

O fluxo para testar as tasks do Celery é:

**1. Dispare a task:**
```bash
curl -X POST "http://localhost:8000/calcular/soma?a=5&b=3"
```

**2. Acompanhe o worker processando em tempo real:**
```bash
docker-compose logs -f celery_worker
```

**3. Verifique a fila:**
```bash
curl "http://localhost:8000/fila_celery"
```

---

## Autenticação

Todos os endpoints (exceto `/healthy`, `/calcular/soma`, `/calcular/fatorial` e `/fila_celery`) requerem autenticação HTTP Basic usando as credenciais configuradas nas variáveis de ambiente `API_USER` e `API_PASSWORD`.

## Sistema de Cache

A API utiliza Redis para cache de consultas de listagem de livros com TTL de 60 segundos. O cache é invalidado automaticamente quando há operações de criação, atualização ou exclusão de livros.

## Sistema de Filas (Celery)

O Celery utiliza o Redis como broker e backend. Tasks computacionalmente pesadas são enviadas para a fila e processadas pelo worker de forma independente, sem bloquear a API. O resultado fica armazenado no Redis e pode ser consultado a qualquer momento pelo `task_id`.

## Modelo de Dados

### Livro (LivroDB)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | Integer | Chave primária (autoincremento) |
| nome_livro | String | Nome do livro (obrigatório) |
| autor_livro | String | Autor do livro (obrigatório) |
| ano_livro | Integer | Ano de publicação (obrigatório) |
