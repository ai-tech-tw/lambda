"""LINE Bot 客戶端與 Webhook 處理器模組 / LINE Bot Client & Webhook Handler Module.

[正體中文]
本模組負責初始化 LINE Messaging API 客戶端實例。
1. `line_bot_api`: 用於向 LINE 平台發送主動訊息或回覆訊息（Reply API）。
2. `handler`: 用於驗證 Webhook 簽章（HMAC-SHA256）並將事件分發給對應的處理函數。

[English]
This module initializes the LINE Messaging API client instances:
1. `line_bot_api`: Used to send push or reply messages via the LINE Messaging API.
2. `handler`: Used to verify webhook signatures (HMAC-SHA256) and dispatch incoming events.
"""

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from config import (
    line_channel_access_token,
    line_channel_secret,
)

# ==============================================================================
# LINE Messaging API 用戶端初始化 / Initialize LINE Messaging API Clients
# ==============================================================================

# [正體中文] 實例化 LineBotApi，傳入長期 Channel Access Token 用於 API 操作（如 reply_message）
# [English] Instantiate LineBotApi with the Channel Access Token for API calls (e.g., reply_message)
line_bot_api = LineBotApi(line_channel_access_token)

# [正體中文] 實例化 WebhookHandler，傳入 Channel Secret 用於驗證請求合法性並路由事件
# [English] Instantiate WebhookHandler with Channel Secret to verify incoming webhooks and route events
handler = WebhookHandler(line_channel_secret)
