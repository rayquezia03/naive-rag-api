# Desafio Técnico — Construção de um Sistema RAG (Retrieval-Augmented Generation)

## Objetivo

O objetivo deste desafio é compreender os fundamentos da arquitetura RAG (Retrieval-Augmented Generation), utilizada para complementar modelos de linguagem com informações externas recuperadas de documentos.

Ao final do desafio, o participante deverá compreender conceitos como:

* Chunking
* Embeddings
* Vector Stores
* Similarity Search
* Retrieval
* Context Augmentation
* Grounding
* Naive RAG
* Re-ranking (bônus)

---

# Contexto

Imagine que precisamos construir um assistente capaz de responder perguntas utilizando informações contidas em documentos fornecidos pelos usuários.

O modelo não deve responder apenas com base em seu conhecimento interno. Antes de gerar uma resposta, ele deve recuperar informações relevantes dos documentos previamente indexados.

Para simplificar o desafio, apenas arquivos Markdown (`.md`) deverão ser suportados.

---

# Objetivo do Projeto

Construir uma aplicação que implemente uma abordagem **Naive RAG**.

A aplicação poderá possuir:

* Interface de linha de comando (CLI)
* API REST
* Interface Web (opcional)

O foco principal do desafio é a compreensão dos conceitos de RAG, e não a construção da interface.

---

# Arquitetura Esperada

## Fluxo de ingestão

Documento → Chunking → Embeddings → Vector Store

## Fluxo de consulta

Pergunta → Retrieval → Contexto Recuperado → LLM → Resposta

---

# Tecnologias

## FastAPI

Utilizado para criação da API REST.

Documentação:

https://fastapi.tiangolo.com/tutorial/

---

## Ollama

Será utilizado obrigatoriamente para execução local dos modelos de chat e embeddings.

Documentação:

https://ollama.com

Instalação:

https://ollama.com/download

Modelos recomendados:

### Chat

* llama3.2:1b
* llama3.2:3b
* qwen2.5:1.5b
* qwen2.5:3b

### Embeddings

* nomic-embed-text
* mxbai-embed-large

Para máquinas com menor capacidade recomenda-se:

```bash
ollama pull llama3.2:1b
ollama pull nomic-embed-text
```

---

## LangChain

Utilizar para:

* Loaders
* Chunking
* Embeddings
* Vector Stores
* Retrieval
* Integração com Ollama

Documentação:

https://docs.langchain.com/oss/python/langchain/rag

---

# Requisitos Funcionais

## RF-01 — Ingestão de Documento

Dado que um usuário envie um arquivo Markdown (`.md`),

o sistema deverá:

* Ler o documento
* Realizar chunking
* Gerar embeddings
* Armazenar os chunks em uma Vector Store

---

## RF-02 — Conversação com RAG

Dado que um usuário realize uma pergunta,

o sistema deverá:

* Recuperar os chunks mais relevantes
* Construir o contexto da consulta
* Enviar contexto e pergunta para o modelo
* Retornar uma resposta baseada nas informações recuperadas

Caso não existam informações suficientes para responder:

* O sistema deverá informar explicitamente que não encontrou informações relevantes
* O sistema não deverá inventar respostas

---

## RF-03 — Exibição de Fontes

Toda resposta deverá retornar os trechos utilizados para gerar a resposta.

Exemplo:

```json
{
  answer: ...,
  sources: [
    {
      chunk: ...,
      score: 0.92
    }
  ]
}
```

---

# Endpoints

## POST /ingest

Responsável pela ingestão dos documentos.

Responsabilidades:

* Receber arquivo Markdown
* Realizar chunking
* Gerar embeddings
* Persistir embeddings

---

## POST /chat

Responsável pela interação com o sistema.

Exemplo de request:

```json
{
  message: Qual é o objetivo do documento?
}
```

Exemplo de response:

```json
{
  answer: ...,
  sources: [
    {
      chunk: ...,
      score: 0.92
    }
  ]
}
```

---

# Requisitos Técnicos

O projeto deverá conter:

* FastAPI
* Ollama
* LangChain
* Vector Store
* Chunking
* Retrieval
* Geração de respostas contextualizadas

---

# Requisitos Bônus

## RF-B01 — Re-ranking

Implementar uma etapa de re-ranking após a recuperação inicial dos documentos.

Objetivo:

Melhorar a qualidade dos documentos enviados ao modelo.

---

## RF-B02 — Interface Web

Criar uma interface para:

* Upload de documentos
* Realização de perguntas
* Exibição das respostas
* Exibição das fontes utilizadas

---

# Entregáveis

O repositório deverá conter:

* Código-fonte
* README com instruções de execução
* Explicação da arquitetura utilizada
* Explicação da estratégia de chunking adotada
* Modelos utilizados
* Limitações encontradas

---

# Critérios de Avaliação

Serão avaliados:

* Clareza da arquitetura
* Organização do código
* Compreensão dos conceitos de RAG
* Qualidade do retrieval
* Estruturação da API
* Tratamento de erros
* Capacidade de justificar decisões técnicas

Mais importante do que fazer funcionar é demonstrar entendimento dos conceitos envolvidos.
