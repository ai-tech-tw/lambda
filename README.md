# lambda

A feature-rich LINE chatbot powered by OpenAI's API with autonomous agent tool-calling capabilities.

## Features

- **Autonomous Agent Loop**: Supports multi-turn tool calling with automatic fallback handling.
- **Web Search**: Real-time web search powered by the [Tavily](https://tavily.com/) API.
- **Academic Paper Search**: Search [arXiv](https://arxiv.org/) for research papers by title, abstract, author, or category.
- **Web Content Extraction**: Scrape and extract readable content from web pages with regex filtering support.
- **Safe Calculator**: Safe AST-based mathematical expression evaluator.
- **World Clock**: Real-time datetime lookup for any IANA timezone.
- **Smart Response Formatting**: Automatically strips internal model reasoning tags (`<think>`) and converts Markdown into clean, readable plain text for LINE messaging.
- **Dual Chat Modes**:
  - **1-on-1 Direct Messages**: Direct conversation without prefixes.
  - **Group Chats**: Responds when messages start with `lambda` (e.g., `lambda what is the latest news on AI?`).

## Prerequisites

- Python >= 3.14
- [`uv`](https://docs.astral.sh/uv/) (Python package and project manager)
- LINE Messaging API Channel ([LINE Developers Console](https://developers.line.biz/))
- OpenAI API Key (or compatible API endpoint)
- Tavily API Key (for web search)

## Environment Configuration

Copy `.env.sample` to `.env` and fill in your configuration:

```bash
cp .env.sample .env
```

| Variable | Description | Default |
| --- | --- | --- |
| `LINE_CHANNEL_ACCESS_TOKEN` | Channel Access Token from LINE Developers Console | Required |
| `LINE_CHANNEL_SECRET` | Channel Secret from LINE Developers Console | Required |
| `OPENAI_BASE_URL` | Base URL for OpenAI API or compatible provider | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | API Key for model provider | Required |
| `OPENAI_CHAT_MODEL` | Model identifier | `gpt-3.5-turbo` |
| `OPENAI_SYSTEM_PROMPT` | Custom system prompt override | Optional |
| `TAVILY_API_KEY` | API Key for Tavily Search | Required for search |
| `AGENT_TIMEOUT_SECONDS` | Agent execution timeout in seconds | `60` |

## Setup

Install the project dependencies using `uv`:

```bash
uv sync
```

## Running the Application

### Development

Run the application with debug mode and auto-reload enabled:

```bash
uv run flask run --debug --reload
```

### Production

Run the application using Gunicorn for production deployments:

```bash
uv run gunicorn -w 4 app:app
```

### Webhook Configuration

Set your LINE Messaging API Webhook URL in the LINE Developers Console to:

```text
https://<your-domain>/callback
```

Make sure **Use webhook** is enabled in the LINE Developers Console.

## Built-in Tools

| Tool | Function | Description |
| --- | --- | --- |
| `current_time` | `tools/clock.py` | Returns the current time in a specified IANA timezone (e.g., `Asia/Taipei`, `UTC`). |
| `evaluate_expression` | `tools/calculator.py` | Safely evaluates arithmetic expressions using AST parsing. |
| `perform_search` | `tools/search.py` | Conducts web searches via Tavily API. |
| `search_papers_dataframe` | `tools/search.py` | Searches arXiv for academic papers and formats summary metadata. |
| `fetch_content` | `tools/content.py` | Fetches readable text from target URLs with optional regex matching and depth traversal. |

## Project Structure

```text
lambda/
├── app.py              # Flask application & LINE webhook handler
├── config.py           # Configuration & environment variables
├── prompts.py          # Agent system prompt
├── clients/
│   ├── line.py         # LINE Bot SDK initialization
│   └── openai.py       # OpenAI async client & agent loop
├── tools/
│   ├── tools.py        # Tool schema definitions & dispatcher
│   ├── calculator.py   # Safe math calculator
│   ├── clock.py        # Timezone clock
│   ├── content.py      # Web scraper & content extractor
│   └── search.py       # Tavily search & arXiv paper search
└── utils/
    ├── markdown.py     # Markdown-to-plain-text stripper
    └── response.py     # Reasoning block (<think>) stripper
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
