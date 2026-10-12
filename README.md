# lambda

[正體中文](README.zh-TW.md) | English

[Join our LINE OpenChat ✨](https://web-tech.tw/ai)

> A friendly, autonomous tool-calling LINE chatbot agent designed for beginners and developers alike.

---

## Overview

**lambda** is an intelligent LINE bot built with Python, Flask, and OpenAI's API (supporting both Responses API and Function Calling).

This project serves as an accessible, beginner-friendly starter for learning **LLM Agents**, **Tool Calling**, and **LINE Messaging API integration**. Unlike traditional chatbots limited to static knowledge, lambda is equipped with an autonomous agent loop that can decide, execute external tools, and synthesize answers:
- When real-time information is requested, it searches the web.
- When arithmetic or calculations are needed, it uses a safe AST math engine rather than hallucinating numbers.
- When research papers are asked for, it queries the arXiv academic database.
- It parses external webpages, extracts clean text, strips internal reasoning tokens (`<think>`), and converts Markdown to readable plain text formatted specifically for LINE.

---

## Features

- 🤖 **Autonomous Agent Loop**: Multi-turn tool execution loop with support for both native function calls and text-advised fallback.
- 🔍 **Real-Time Web Search**: Powered by the [Tavily Search API](https://tavily.com/) for up-to-date web results.
- 📚 **Academic Paper Search**: Queries [arXiv](https://arxiv.org/) for papers by title, abstract, author, or category.
- 🌐 **Web Scraping & Extraction**: Extracts readable text from URLs using Scrapy & Requests, with depth crawling and regex pattern filtering.
- 🧮 **Safe Math Calculator**: Evaluates arithmetic expressions safely using Python's Abstract Syntax Tree (AST).
- 🕒 **World Clock**: Looks up current timestamps across any IANA timezone.
- 🧹 **LINE Text Optimization**: Automatically strips `<think>...</think>` internal model thoughts and converts Markdown into clean, uncluttered plain text.
- 👥 **Dual Conversation Modes**:
  - **1-on-1 Direct Messages**: Directly chat with the bot.
  - **Group Chats**: Bot responds whenever a message starts with `lambda` (e.g., `lambda what is the latest AI news?`).

---

## Prerequisites

Before getting started, make sure you have the following installed on your system:

- **Python >= 3.14**: We recommend the latest stable Python release.
- [**uv**](https://docs.astral.sh/uv/): An extremely fast Python package and project manager. Install it via:
  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **LINE Messaging API Channel**: Create a channel at the [LINE Developers Console](https://developers.line.biz/) to get your credentials.
- **OpenAI API Key**: Or an OpenAI-compatible endpoint (such as Nymph Gateway).
- **Tavily API Key**: Required for web searches (sign up for free at [Tavily](https://tavily.com/)).

---

## Environment Configuration

Copy the sample environment file `.env.sample` to `.env`:

```bash
cp .env.sample .env
```

Open `.env` in your editor and configure the following variables:

| Variable | Description | Example / Default | Required |
| --- | --- | --- | --- |
| `LINE_CHANNEL_ACCESS_TOKEN` | Long-lived channel access token from LINE Developers | From LINE Developers Console | **Yes** |
| `LINE_CHANNEL_SECRET` | Channel secret from LINE Developers | From LINE Developers Console | **Yes** |
| `OPENAI_BASE_URL` | Base URL for OpenAI API or compatible gateway | `https://api.openai.com/v1` | Optional |
| `OPENAI_API_KEY` | API Key for model provider | `sk-...` | **Yes** |
| `OPENAI_CHAT_MODEL` | Chat model identifier | `gpt-3.5-turbo` | Optional |
| `OPENAI_SYSTEM_PROMPT` | Custom system prompt override | `None` (uses built-in prompt) | Optional |
| `TAVILY_API_KEY` | API Key for Tavily Search | `tvly-...` | **Yes for search** |
| `AGENT_TIMEOUT_SECONDS` | Maximum timeout for agent execution in seconds | `60` | Optional |

---

## Setup & Installation

Install dependencies and set up the virtual environment in one command using `uv`:

```bash
uv sync
```

---

## Running the Application

### 1. Development Mode

Start the Flask development server with auto-reload and debug mode enabled:

```bash
uv run flask run --debug --reload
```
By default, the server listens at `http://127.0.0.1:5000/`.

### 2. Production Mode

Run with the high-performance Gunicorn WSGI server:

```bash
uv run gunicorn -w 4 app:app
```

---

## LINE Webhook Configuration

1. Expose your server to HTTPS using a reverse proxy, Cloudflare Tunnel, or ngrok.
2. In the [LINE Developers Console](https://developers.line.biz/), select your Messaging API channel.
3. Under the **Messaging API** tab, set the **Webhook URL** to:
   ```text
   https://<your-domain>/callback
   ```
4. Enable the **Use webhook** toggle.
5. Click **Verify** to confirm the connection, and start chatting with your bot on LINE!

---

## Built-in Tools

lambda's built-in tools are organized in the `tools/` directory:

| Tool Name (`name`) | Location | Description |
| --- | --- | --- |
| `current_time` | [tools/clock.py](tools/clock.py) | Returns current date and time for a given IANA timezone (e.g., `Asia/Taipei`, `UTC`). |
| `evaluate_expression` | [tools/calculator.py](tools/calculator.py) | Safely evaluates arithmetic expressions using AST parsing to avoid code injection. |
| `perform_search` | [tools/search.py](tools/search.py) | Performs real-time web searches using Tavily API. |
| `search_papers_dataframe` | [tools/search.py](tools/search.py) | Queries arXiv for academic papers and formats summary metadata. |
| `fetch_content` | [tools/content.py](tools/content.py) | Fetches text from URLs with recursive depth traversal and regex pattern matching. |

---

## Project Structure

```text
lambda/
├── app.py              # Flask webhook endpoint and LINE event handler
├── config.py           # Centralized configuration and environment loading
├── prompts.py          # AI agent default system prompt and persona
├── clients/
│   ├── line.py         # LINE Bot SDK initialization
│   └── openai.py       # Async OpenAI client and agent multi-turn loop
├── tools/
│   ├── __init__.py     # Module exports
│   ├── tools.py        # Tool schema definitions, validation, and dispatcher
│   ├── calculator.py   # Safe AST arithmetic calculator
│   ├── clock.py        # Timezone clock lookup
│   ├── content.py      # Web scraper and text extractor
│   └── search.py       # Tavily web search and arXiv academic paper search
├── utils/
│   ├── __init__.py     # Utility package exports
│   ├── markdown.py     # Markdown-to-plain-text stripper for clean LINE messages
│   └── response.py     # Filter for internal reasoning blocks (<think>)
├── pyproject.toml      # Project metadata and dependencies (uv / PEP 621)
├── uv.lock             # Deterministic dependency lockfile
├── .env.sample         # Sample environment variable template
└── LICENSE             # MIT Open Source License
```

---

## License

This project is open-source software licensed under the [MIT License](LICENSE).
