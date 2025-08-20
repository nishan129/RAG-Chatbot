import pymongo
from app.config.config import DATABASE_NAME, COLLECTION_NAME
import certifi
import os
ca = certifi.where()
class MongoDBClient:
    client = None
    def __init__(self, database_name=DATABASE_NAME) -> None:
        try:

            if MongoDBClient.client is None:
                mongo_db_url = os.getenv('MONGODB_URL_KEY',"mongodb+srv://nishantborkar139:5QnjppwOKto3jwD0@cluster0.oc0m3gh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
                print(mongo_db_url)
                if "localhost" in mongo_db_url:
                    MongoDBClient.client = pymongo.MongoClient(mongo_db_url) 
                else:
                    MongoDBClient.client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)
            self.client = MongoDBClient.client
            self.database = self.client[database_name]
            self.database_name = database_name
        except Exception as e:
            raise e