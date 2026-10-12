"""專案設定與環境變數載入模組 / Configuration and Environment Variables Module.

[正體中文]
本模組負責在應用程式啟動時載入 `.env` 檔案中的環境變數，並提供給專案其他模組使用。
專為初學者設計，集中管理所有 API 金鑰、端點與運作參數，避免敏感資訊硬編碼在原始碼中。
支援 OpenAI、NVIDIA NIM（NVIDIA Inference Microservices）或 Nymph 社群免費轉換閘道。

[English]
This module is responsible for loading environment variables from the `.env` file upon
application startup and providing them to other modules throughout the project.
Centralizing API credentials, endpoints, and operational parameters helps prevent
hardcoding secrets into the source code.
Supports OpenAI, NVIDIA NIM (NVIDIA Inference Microservices), or the Nymph community gateway.
"""

from os import getenv
from dotenv import load_dotenv

# [正體中文] 載入同目錄下的 .env 檔案內容至環境變數
# [English] Load environment variables from the local .env file into the system environment
load_dotenv()

# ==============================================================================
# LINE Messaging API 設定 / LINE Messaging API Credentials
# ==============================================================================
# [正體中文] LINE 頻道的長期存取權杖（Channel Access Token），用於呼叫 LINE API 發送訊息
# [English] Long-lived channel access token used to authenticate calls to the LINE Messaging API
line_channel_access_token = getenv("LINE_CHANNEL_ACCESS_TOKEN")

# [正體中文] LINE 頻道的密鑰（Channel Secret），用於驗證 Webhook 請求簽章（X-Line-Signature）
# [English] Channel secret used to verify webhook request signatures to ensure requests come from LINE
line_channel_secret = getenv("LINE_CHANNEL_SECRET")

# ==============================================================================
# 模型供應商設定 / Model Provider Credentials
# 支援 OpenAI、NVIDIA NIM 或 Nymph 相容閘道
# ==============================================================================
# [正體中文] API 伺服器基礎端點：
# - 官方 OpenAI: https://api.openai.com/v1
# - NVIDIA NIM: https://integrate.api.nvidia.com/v1
# - Nymph 免費閘道: https://web-tech.tw/recv/openai/v1
# [English] Base URL for the model provider API:
# - Official OpenAI: https://api.openai.com/v1
# - NVIDIA NIM: https://integrate.api.nvidia.com/v1
# - Nymph Community Gateway: https://web-tech.tw/recv/openai/v1
openai_base_url = getenv("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1")

# [正體中文] 模型供應商的 API 金鑰（如 NVIDIA NIM nvapi-... 或 OpenAI 金鑰）
# [English] API key for authenticating with the model provider (e.g. NVIDIA NIM nvapi key, OpenAI key)
openai_api_key = getenv("OPENAI_API_KEY")

# [正體中文] 使用的對話模型名稱（預設為 NVIDIA NIM 之 openai/gpt-oss-20b）
# [English] Name of the chat completion model to use (defaults to openai/gpt-oss-20b)
openai_chat_model = getenv("OPENAI_CHAT_MODEL", "openai/gpt-oss-20b")

# [正體中文] 自訂系統提示詞覆寫值（若未設定則在 prompts.py 中使用預設提示詞）
# [English] Optional custom system prompt override (defaults to DEFAULT_PROMPT if unset)
openai_system_prompt = getenv("OPENAI_SYSTEM_PROMPT")

# ==============================================================================
# 智慧代理（Agent）運作與工具設定 / Agent & External Tools Configuration
# ==============================================================================
# [正體中文] Agent 單次處理的最長逾時秒數（預設為 60 秒），防止模型工具迴圈陷入無窮等待
# [English] Maximum execution timeout in seconds for agent processing (default 60s) to avoid hanging
agent_timeout_seconds = int(getenv("AGENT_TIMEOUT_SECONDS", "60"))

# [正體中文] Tavily 網路搜尋服務的 API 金鑰，若啟用 perform_search 工具時必須設定
# [English] API key for the Tavily web search service; required when perform_search is invoked
tavily_api_key = getenv("TAVILY_API_KEY")
