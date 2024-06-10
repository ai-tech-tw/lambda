from os import getenv
from dotenv import load_dotenv

load_dotenv()

line_channel_access_token = getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_channel_secret = getenv("LINE_CHANNEL_SECRET")

openai_base_url = getenv("OPENAI_BASE_URL")
openai_api_key = getenv("OPENAI_API_KEY")
openai_chat_model = getenv("OPENAI_CHAT_MODEL")
