from flask import Flask, request, abort

from clients.openai import chat_with_ai

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from config import (
    line_channel_access_token,
    line_channel_secret,
)

# LINE Messaging API config
line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)

# Flask config
app = Flask(__name__)


# Webhook endpoint
@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# Message event handler
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Ignore non-text-message event
    if not isinstance(event.message, TextMessage):
        return

    # Get text from the message
    is_from_dm = event.source.type == "user"
    user_text = event.message.text

    # Check if the text starts with "lambda"
    if not user_text.startswith("lambda") and not is_from_dm:
        return

    # Remove the prefix
    user_text = user_text.lstrip("lambda")

    # Generate response
    ai_text = chat_with_ai(user_text)

    # Check completion
    if not ai_text:
        return

    # Reply to the user with the generated response
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_text.strip()),
    )
