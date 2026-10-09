# lambda

A simple chat bot based on chat completion API.

## Prerequisites

It's required to have the following installed on your machine:

- python >= 3.9
- uv

## Setup

To install the dependencies, run the following command:

```bash
uv sync
```

## Run

Depending on the environment, you can run the application using the following commands:

### Development

Run the application using the following command with the debug mode enabled and auto-reload:

```bash
uv run flask run --debug --reload
```

### Production

Run the application using the following command with the gunicorn server for better performance:

```bash
uv run gunicorn -w 4 app:app
```
