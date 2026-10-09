from os import getenv
from dotenv import load_dotenv

load_dotenv()

line_channel_access_token = getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_channel_secret = getenv("LINE_CHANNEL_SECRET")

openai_base_url = getenv("OPENAI_BASE_URL")
openai_api_key = getenv("OPENAI_API_KEY")
openai_chat_model = getenv("OPENAI_CHAT_MODEL")
openai_system_prompt = getenv("OPENAI_SYSTEM_PROMPT")

agent_timeout_seconds = int(getenv("AGENT_TIMEOUT_SECONDS", "60"))
tavily_api_key = getenv("TAVILY_API_KEY")
