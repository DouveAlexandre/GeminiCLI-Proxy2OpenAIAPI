# Gemini 2 OpenAI Proxy

This program is a wrapper for [Gemini CLI](https://github.com/google-gemini/gemini-cli) that can serve **Google Gemini 2.5 Pro** (or Flash) through an **OpenAI-compatible API**.
It works plug-and-play with clients that already speak OpenAI like SillyTavern, llama.cpp, LangChain, VS Code's *Cline* extension, etc.

---

## Features

| ✔ | Feature | Notes |
|---|---------|-------|
| `/v1/chat/completions` | Non-stream & stream (SSE) | Works with curl, ST, LangChain… |
| Vision support | `image_url` → Gemini `inlineData` | |
| Function / Tool calling | OpenAI "functions" → Gemini Tool Registry | |
| Reasoning / chain-of-thought | Sends `enable_thoughts:true`, streams `<think>` chunks | ST shows gray bubbles |
| 1M token context | Proxy auto-elevates Gemini CLI's default 200k limit | |
| CORS | Enabled (`*`) by default | Ready for browser apps |

---

## Quick Start

### With npm

```bash
git clone https://github.com/DouveAlexandre/GeminiCLI-Proxy2OpenAIAPI
cd GeminiCLI-Proxy2OpenAIAPI
npm i
npm start # starts the server (runs on port 11434 by default)
```

### With Docker

Alternatively, you can use the provided Dockerfile to build a Docker image.

```sh
docker build --tag "GeminiCLI-Proxy2OpenAIAPI" .
docker run -p 11434:80 -e GEMINI_API_KEY=your_key_here GeminiCLI-Proxy2OpenAIAPI
```

---

## .env File Configuration

The application uses an `.env` file for configuration. Create an `.env` file in the project root with the following variables:

### Basic Configuration

```env
# Port where the server will run
PORT=11434

# Authentication type - can be 'oauth-personal', 'gemini-api-key', or 'vertex-ai'
AUTH_TYPE=oauth-personal

# Path to OAuth credentials (only for AUTH_TYPE='oauth-personal')
GOOGLE_APPLICATION_CREDENTIALS=C:\Users\your_user\.gemini\oauth_creds.json

# Gemini API Key (only for AUTH_TYPE='gemini-api-key')
GEMINI_API_KEY=

# Model to be used - 'gemini-2.5-flash' or 'gemini-2.5-pro'
# Leave empty to use CLI default model
MODEL=
```

### Authentication Types

#### 1. OAuth Personal (Recommended for personal use)
```env
AUTH_TYPE=oauth-personal
GOOGLE_APPLICATION_CREDENTIALS=C:\Users\your_user\.gemini\oauth_creds.json
```
- **Advantages**: Free access to Gemini 2.5 Pro
- **How to configure**: Log in to your Google account through Gemini CLI
- **Requirements**: Gemini CLI configured with OAuth

#### 2. Gemini API Key
```env
AUTH_TYPE=gemini-api-key
GEMINI_API_KEY=your_api_key_here
```
- **Advantages**: Simpler to configure
- **How to obtain**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Requirements**: Valid Google AI API key

#### 3. Vertex AI
```env
AUTH_TYPE=vertex-ai
```
- **Usage**: For corporate environments with Vertex AI
- **Requirements**: Additional Google Cloud configuration

### Model Configuration

```env
# To use Gemini 2.5 Flash (faster, less accurate)
MODEL=gemini-2.5-flash

# To use Gemini 2.5 Pro (slower, more accurate)
MODEL=gemini-2.5-pro

# Leave empty to use default model
MODEL=
```

---

## How to Use

### 1. Initial Setup

1. Clone the repository and install dependencies:
```bash
git clone https://github.com/DouveAlexandre/GeminiCLI-Proxy2OpenAIAPI
cd GeminiCLI-Proxy2OpenAIAPI
npm install
```

2. Create the `.env` file with your settings (see section above)

3. Start the server:
```bash
npm start
```

The server will be available at `http://localhost:11434`

### 2. Test with curl

```bash
curl -X POST http://localhost:11434/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gemini-2.5-pro",
       "messages": [{"role": "user", "content": "Hello Gemini!"}]
     }'
```

### 3. SillyTavern Configuration

1. Go to **API Connections**
2. Select **Chat Completion (OpenAI, Claude, Window/OpenRouter, Scale)**
3. Configure:
   - **API**: OpenAI
   - **API Base URL**: `http://127.0.0.1:11434/v1/chat/completions`
   - **API Key**: any value (not used)
   - **Model**: `gemini-2.5-pro` or `gemini-2.5-flash`

### 4. VS Code Configuration (Cline)

1. Install the Cline extension
2. Configure:
   - **Provider**: OpenAI Compatible
   - **Base URL**: `http://localhost:11434/v1/chat/completions`
   - **API Key**: any value
   - **Model**: `gemini-2.5-pro`

### 5. Using with LangChain (Python)

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:11434/v1/chat/completions",
    api_key="any-value",
    model="gemini-2.5-pro-latest"
)

response = llm.invoke("Hello, how are you?")
print(response.content)
```

---

## Advanced Features

### Image Support

```bash
curl -X POST http://localhost:11434/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gemini-2.5-pro-latest",
       "messages": [{
         "role": "user",
         "content": [
           {"type": "text", "text": "Describe this image"},
           {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
         ]
       }]
     }'
```

### Streaming

```bash
curl -X POST http://localhost:11434/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gemini-2.5-pro-latest",
       "messages": [{"role": "user", "content": "Tell me a story"}],
       "stream": true
     }'
```

### Function Calling

```bash
curl -X POST http://localhost:11434/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gemini-2.5-pro-latest",
       "messages": [{"role": "user", "content": "What's the weather today?"}],
       "tools": [{
         "type": "function",
         "function": {
           "name": "get_weather",
           "description": "Get weather information",
           "parameters": {
             "type": "object",
             "properties": {
               "location": {"type": "string", "description": "Location"}
             }
           }
         }
       }]
     }'
```

---

## Solução de Problemas

### Erro de Autenticação OAuth
- Verifique se o caminho em `GOOGLE_APPLICATION_CREDENTIALS` está correto
- Execute `gemini auth` no terminal para reautenticar

### Erro de API Key
- Verifique se a chave em `GEMINI_API_KEY` é válida
- Confirme se `AUTH_TYPE=gemini-api-key`

### Servidor não inicia
- Verifique se a porta especificada em `PORT` está disponível
- Confirme se todas as dependências foram instaladas com `npm install`

### Modelo não encontrado
- Use `gemini-2.5-pro` ou `gemini-2.5-flash` como nome do modelo
- Deixe `MODEL` vazio no .env para usar o padrão

---

## Licença

MIT – livre para uso pessoal e comercial. Fork de https://huggingface.co/engineofperplexity/gemini-openai-proxy
