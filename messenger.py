import telegram
import config

class Messenger:
    def __init__(self):
        self.bot = telegram.Bot(token=config.TOKEN)

    def send(self, message):
        self.bot.sendMessage(chat_id=config.CHAT_ID, text=message)



