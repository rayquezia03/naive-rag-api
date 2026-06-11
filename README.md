# Naive RAG — Desafio Técnico

API REST que implementa **Naive RAG** (Retrieval-Augmented Generation) sobre documentos Markdown, utilizando FastAPI, LangChain, Ollama e ChromaDB.

---

## Arquitetura

```
FLUXO DE INGESTÃO
─────────────────
Arquivo Markdown
    │
    ▼
TextLoader  (LangChain)
    │  lê o texto bruto preservando a estrutura
    ▼
RecursiveCharacterTextSplitter  (LangChain)
    │  divide por títulos → parágrafos → frases
    ▼
OllamaEmbeddings  (nomic-embed-text)
    │  converte cada chunk em um vetor denso
    ▼
ChromaDB  (persistido localmente)
    │  armazena vetores + texto bruto + metadados


FLUXO DE CONSULTA
─────────────────
Pergunta do usuário
    │
    ▼
OllamaEmbeddings  (mesmo modelo)
    │  codifica a pergunta em vetor
    ▼
ChromaDB similarity_search
    │  retorna os 13 chunks mais similares (k_fetch=13)
    ▼
FlashrankRerank  (cross-encoder)
    │  reordena os candidatos, mantém os 8 mais relevantes
    ▼
PromptTemplate
    │  monta o contexto numerado em torno da pergunta
    ▼
OllamaLLM  (llama3.2:3b)
    │  gera a resposta baseada no contexto
    ▼
Resposta JSON  { answer, sources: [{ chunk, score, source }] }
```

---

## Estratégia de Chunking

**Método:** `RecursiveCharacterTextSplitter` com separadores orientados a Markdown.

O splitter tenta dividir o texto nos seguintes limites, em ordem de prioridade:

| Prioridade | Separador | Justificativa |
|-----------|-----------|---------------|
| 1 | `\n## ` | Título H2 — limite de tópico |
| 2 | `\n### ` | Título H3 — limite de subtópico |
| 3 | `\n#### ` | Título H4 |
| 4 | `\n\n` | Quebra de parágrafo |
| 5 | `\n` | Quebra de linha |
| 6 | ` ` | Limite de palavra |
| 7 | `""` | Caractere (último recurso) |

**Parâmetros (configuráveis via `.env`):**

| Parâmetro | Padrão | Justificativa |
|-----------|--------|---------------|
| `CHUNK_SIZE` | 500 | Cabe na janela de contexto de modelos de embedding pequenos; grande o suficiente para preservar uma ideia coerente |
| `CHUNK_OVERLAP` | 50 | Evita cortar o contexto nas bordas sem inflar significativamente o armazenamento |

Priorizar separadores de título garante chunks semanticamente coerentes que permanecem dentro da mesma seção, o que melhora a precisão do retrieval em documentos estruturados como especificações e relatórios.

---

## Modelos

| Função | Modelo | Observações |
|--------|--------|-------------|
| Embeddings | `nomic-embed-text` | Rápido, alta qualidade, executa localmente via Ollama |
| Chat / Geração | `llama3.2:3b` | Modelo de 3B parâmetros; configurável via `.env` |

---

## Pré-requisitos

- Python 3.10+
- [Ollama](https://ollama.com/download) instalado e em execução

1. Baixe os modelos necessários:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

2. Certifique-se de que o Ollama está rodando:

```bash
ollama serve
```

---

## Instalação e Execução

```bash
# Acesse o diretório do projeto
cd iphan-project

# Crie o ambiente virtual (Python 3.10+)
python -m venv .venv
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# (Opcional) ajuste modelos ou tamanho do chunk
# edite o arquivo .env

# Inicie a API
uvicorn app.main:app --reload
```

> **Atenção:** Na primeira requisição que acionar o re-ranking, o Flashrank fará o download automático de um modelo cross-encoder pequeno (~80 MB). Certifique-se de ter acesso à internet na primeira execução.

A API estará disponível em `http://localhost:8000`.  
Documentação interativa: `http://localhost:8000/docs`  
Interface web: `http://localhost:8000`

---

## Endpoints

### `POST /ingest`

Envia um arquivo Markdown para indexação.

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@meu_documento.md"
```

Resposta:
```json
{ "chunks_stored": 12, "filename": "meu_documento.md" }
```

Apenas arquivos `.md` são aceitos. Outros formatos retornam HTTP 400.

---

### `POST /chat`

Realiza uma pergunta sobre os documentos indexados.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual é o objetivo principal do documento?"}'
```

Resposta:
```json
{
  "answer": "O objetivo principal é ...",
  "sources": [
    {
      "chunk": "...",
      "score": 0.9241,
      "source": "meu_documento.md"
    }
  ]
}
```

> **Nota sobre o score:** Após o re-ranking, o score é uma **pontuação de relevância** (maior = mais relevante). Um valor próximo de `1.0` indica correspondência muito forte entre o chunk e a pergunta.

---

### `GET /health`

Verifica se a API e o Ollama estão operacionais.

```bash
curl http://localhost:8000/health
# {"status": "ok", "ollama": true}
```

---

## Funcionalidades Bônus

### RF-B01 — Re-ranking

Após a busca inicial por similaridade, um cross-encoder **FlashrankRerank** reavalia cada chunk candidato em relação à pergunta. Essa abordagem em dois estágios compensa a lacuna semântica entre similaridade de embeddings e relevância real:

- Estágio 1 (revocação): ChromaDB busca os 13 candidatos mais similares por vetor
- Estágio 2 (precisão): Flashrank reavalia e reordena, mantendo os 8 mais relevantes

O Flashrank utiliza um modelo cross-encoder leve que executa localmente, sem necessidade de GPU ou PyTorch.

### RF-B02 — Interface Web

Uma interface single-page é servida em `http://localhost:8000` com:

- Upload de arquivos por clique ou arrastar e soltar
- Chat com animação de digitação
- Painéis de fontes recolhíveis com scores coloridos por relevância
- Lista de arquivos indexados na barra lateral
- Indicador de status do Ollama em tempo real

---

## Limitações

- **Apenas arquivos Markdown (`.md`)** são suportados por definição do projeto.
- O vector store **não é isolado por sessão** — todos os documentos ingeridos compartilham a mesma coleção do Chroma. As consultas sempre buscam em todo o conteúdo indexado.
- Modelos locais pequenos podem produzir respostas incompletas para perguntas amplas que exigem síntese de múltiplas seções do documento. Perguntas mais específicas geram respostas mais precisas.
- Nenhuma autenticação ou limitação de requisições está implementada — trata-se de um ambiente de desenvolvimento local.
- O ChromaDB armazena os vetores em disco em `./vector_store`. Apagar essa pasta remove todos os documentos indexados.

---

## Estrutura do Projeto

```
iphan-project/
├── app/
│   ├── main.py              # Aplicação FastAPI + registro de rotas + interface web
│   ├── core/
│   │   └── config.py        # Configurações lidas do .env
│   ├── routes/
│   │   ├── ingest.py        # POST /ingest
│   │   └── chat.py          # POST /chat
│   ├── services/
│   │   ├── vector_store.py  # Singleton do ChromaDB
│   │   ├── ingestion.py     # Carregar → chunkar → embedar → armazenar
│   │   └── retrieval.py     # Recuperar → re-rankar → promtar → gerar
│   └── static/
│       └── index.html       # Interface web single-page
├── .env                     # Configuração padrão
├── requirements.txt
└── README.md
```
