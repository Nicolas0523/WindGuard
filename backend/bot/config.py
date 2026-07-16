from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    bot_token: str 

def settings() -> Settings:
    return Settings(
        bot_token=os.environ["BOT_TOKEN"]
    )