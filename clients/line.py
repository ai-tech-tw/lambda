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
