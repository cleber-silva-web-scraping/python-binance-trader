import pymongo
import config

connection_string = "mongodb+srv://{}:{}@{}/?retryWrites=true&w=majority".format(config.MONGO_USER, config.MONGO_PASSWORD, config.MONGO_URL)
client = pymongo.MongoClient(connection_string)
mydb = client["binance"]
orders = mydb["orders"]

