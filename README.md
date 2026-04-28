# ML Telegram App

This project is a small multi-service Telegram chatbot stack:

- `telegram_bot`: receives Telegram messages and forwards them to the API.
- `api`: orchestrates chat requests, stores conversation history, and calls the LLM service.
- `llm_service`: thin wrapper around local Ollama HTTP endpoints.
- `db`: PostgreSQL database used by the API for conversations/messages.

The main behavior is "stateful chat per Telegram chat id": each user/chat gets a conversation in Postgres, recent history is loaded, and that context is sent to the model before generating a reply.

## How it works

1. A user sends a message to the Telegram bot.
2. The bot sends `user_id` (Telegram chat id) and `prompt` to `api /chat`.
3. The API:
   - gets or creates a conversation for that user,
   - loads recent messages,
   - prepends a system message,
   - calls `llm_service /chat`.
4. `llm_service` forwards the request to Ollama (`/api/chat`).
5. API stores both user + assistant messages in Postgres.
6. Bot sends the assistant response back to Telegram.

## Tech stack

- Python + FastAPI
- SQLModel + PostgreSQL
- Ollama (external/local runtime)
- Telegram Bot API (`python-telegram-bot`)
- Docker Compose

## Project structure

- `telegram_bot/bot.py`: Telegram polling bot and API client calls.
- `api/main.py`: public API endpoints and chat orchestration.
- `api/database.py`: SQLModel schemas and DB helper functions.
- `llm_service/llm_model.py`: Ollama proxy service.
- `docker-compose.yaml`: local multi-container setup.

## Prerequisites

- Docker + Docker Compose
- A running Ollama server accessible at `http://host.docker.internal:11434`
- A Telegram bot token

## Environment variables

Create a `.env` file in the project root for the `telegram_bot` service:

```env
TELEGRAM_HTTP_API=your_telegram_bot_token
CHAT_ID=your_chat_id_for_startup_message
```

Notes:

- `API_URL` is injected by Docker Compose (`http://api:8001`) for the bot.
- `DATABASE_URL` and `LLM_SERVICE_URL` are injected for the API by Docker Compose.
- You can tune API context window using `MAX_HISTORY_MESSAGES` (default `12`).

## Run locally

```bash
docker compose up --build
```

Services:

- `llm_service`: `http://localhost:8000`
- `api`: `http://localhost:8001`
- `db`: `localhost:5432`

## Useful API endpoints

- `GET /health` (API and LLM service): health checks
- `GET /models` (API): list available models from Ollama
- `POST /chat` (API): chat endpoint used by Telegram bot
- `GET /conversations` (API): list stored conversations
- `GET /conversations/{conversation_id}/messages` (API): get message history

Example request:

```json
{
  "user_id": "123456789",
  "prompt": "Hello, what can you do?"
}
```

## Development notes

- The API creates DB tables on startup.
- Compose uses health checks and service dependencies, so `api` waits for `db` and `llm_service`.
- `llm_service` currently exposes both `/generate` and `/chat`; API uses `/chat`.
