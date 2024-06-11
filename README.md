# lambda

A simple chat bot based on chat completion API.

## Prerequisites

It's required to have the following installed on your machine:

- python 3.7
- pip

## Setup

To install the dependencies, run the following command:

```bash
pip install -r requirements.txt
```

## Run the development server

Run the application using the following command with the debug mode enabled and auto-reload:

```bash
flask run --debug --reload
```

### Run the production server

Run the application using the following command with the gunicorn server for better performance:

```bash
gunicorn -w 4 app:app
```
