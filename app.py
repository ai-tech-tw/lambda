"""Flask Webhook 伺服器與 LINE 訊息處理進入點 / Flask Webhook Server & LINE Handler Entry Point.

[正體中文]
本檔案為整套系統的主要進入點（Entry Point）：
1. 建立 Flask 網頁伺服器，對外提供 `/callback` 路由接收 LINE Webhook 請求。
2. 驗證來自 LINE 伺服器的數位簽章（HMAC-SHA256），確保訊息來源安全無虞。
3. 監聽文字訊息事件（TextMessage），依據私聊或群組判斷是否觸發機器人。
4. 調用 OpenAI Agent 進行智慧推論與外部工具調用。
5. 去除回應中的思考標籤（<think>）與 Markdown 符號，透過 LINE Reply API 回覆使用者。

[English]
This file serves as the main entry point for the application:
1. Initializes the Flask web server and provides the `/callback` endpoint for LINE webhooks.
2. Validates digital signatures (HMAC-SHA256) from LINE servers to ensure security.
3. Listens for TextMessage events, determining triggers based on DM or group context.
4. Invokes the OpenAI agent loop for reasoning and external tool execution.
5. Cleans up internal reasoning tags (<think>) and Markdown formatting before replying to LINE.
"""

from asyncio import run as asyncio_run

from flask import Flask, request, abort

from clients.line import handler, line_bot_api
from clients.openai import chat_with_ai
from utils.markdown import strip_markdown
from utils.response import strip_thinking

from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ==============================================================================
# Flask 應用程式初始化 / Flask Application Initialization
# ==============================================================================
app = Flask(__name__)


# ==============================================================================
# LINE Webhook 接收端點 / LINE Webhook Endpoint
# ==============================================================================
@app.route("/callback", methods=["POST"])
def callback():
    """接收並處理來自 LINE Messaging API 的 Webhook 請求 / Handle LINE Webhook requests.

    [正體中文]
    LINE 伺服器會在使用者發送訊息時，透過 POST 請求將事件資料發送到此端點。
    每個請求都會附帶 `X-Line-Signature` HTTP 標頭，用於驗證請求確實來自 LINE。

    [English]
    The LINE platform sends HTTP POST requests containing event objects to this endpoint.
    Every request contains an `X-Line-Signature` header to prove authenticity.
    """
    # [正體中文] 取得 HTTP 標頭中的數位簽章
    # [English] Retrieve the digital signature from the request headers
    signature = request.headers["X-Line-Signature"]

    # [正體中文] 取得請求主體（Request Body）的純文字內容
    # [English] Retrieve the raw request body text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # [正體中文] 驗證簽章並交由 WebhookHandler 處理分發事件
    # [English] Verify signature and pass body to handler for event dispatching
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        # [正體中文] 簽章無效時回傳 HTTP 400 Bad Request 中止請求
        # [English] Abort with HTTP 400 if the signature verification fails
        abort(400)

    # [正體中文] LINE 規定 Webhook 必須回傳 200 OK，否則會重試或視為失敗
    # [English] Return "OK" with HTTP status 200 as required by LINE Webhook specifications
    return "OK"


# ==============================================================================
# LINE 文字訊息事件處理器 / Message Event Handler
# ==============================================================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理收到的文字訊息事件 / Handle incoming TextMessage events.

    [正體中文]
    當使用者在 LINE 中傳送文字訊息時，此函數會被自動觸發。
    處理流程包含：
    1. 過濾非純文字訊息。
    2. 檢查觸發條件（一對一私聊直接回應；群組中需以 `lambda` 開頭）。
    3. 呼叫非同步 Agent 函數 `chat_with_ai` 產生回答。
    4. 清理回答中的 Markdown 與推理標籤。
    5. 透過 LINE SDK 發送回覆訊息。

    [English]
    Automatically triggered when a user sends a text message in LINE.
    Processing pipeline:
    1. Filter out non-text messages.
    2. Check trigger conditions (DM responds directly; group requires 'lambda' prefix).
    3. Call the asynchronous agent function `chat_with_ai`.
    4. Clean Markdown formatting and thinking tags from the response.
    5. Reply back to the user using the LINE SDK.
    """
    # [正體中文] 忽略非文字訊息事件（例如貼圖、圖片、語音等）
    # [English] Ignore non-text message events (e.g. stickers, images, audio)
    if not isinstance(event.message, TextMessage):
        return

    # [正體中文] 判斷訊息來源：若 source.type 為 "user" 代表是一對一私訊
    # [English] Determine message source: 'user' indicates a 1-on-1 private chat
    is_from_dm = event.source.type == "user"
    user_text = event.message.text

    # [正體中文] 在群組或聊天室中，只有以 "lambda" 開頭的訊息才會觸發機器人，避免洗版干擾
    # [English] In groups or multi-user rooms, only trigger if prefixed with "lambda" to prevent spam
    if not user_text.startswith("lambda") and not is_from_dm:
        return

    # [正體中文] 去除 "lambda" 前綴詞，取得使用者真正詢問的內容
    # [English] Strip the leading "lambda" keyword to extract the actual query
    user_text = user_text.lstrip("lambda")

    # [正體中文] 取得發送者 User ID，作為後續對話或身分識別用途
    # [English] Get the sender's user_id for identification / session tracking
    user_id = getattr(event.source, "user_id", None)

    # [正體中文] 調用非同步 AI 聊天代理處理使用者問題與多輪工具調用
    # [English] Execute the asynchronous AI agent function to reason and execute tools
    result = asyncio_run(chat_with_ai(user_id, user_id, user_text))

    # [正體中文] 去除模型推理過程（<think>標籤）並移除 Markdown 語法，使 LINE 介面閱讀更清爽
    # [English] Strip thinking blocks (<think>) and Markdown syntax for cleaner display on LINE
    ai_text = strip_markdown(strip_thinking(result["answer"]))

    # [正體中文] 若回答為空則不發送訊息
    # [English] Do not reply if the generated text is empty
    if not ai_text:
        return

    # [正體中文] 透過 reply_token 將 AI 回覆內容傳送給 LINE 使用者
    # [English] Reply back to the user via LINE Messaging API using the event's reply_token
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_text.strip()),
    )
