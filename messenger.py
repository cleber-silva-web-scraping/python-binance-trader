import config
import json
import requests
import urllib


class Messenger:
    def __init__(self):
        self.url = "https://api.telegram.org/bot{}/".format(config.TOKEN)
        self.send("Iniciando.")

    def send(self, message):
        tot = urllib.parse.quote_plus(message)
        url = self.url + "sendMessage?text={}&chat_id={}".format(tot, config.CHAT_ID)
        requests.get(url)
