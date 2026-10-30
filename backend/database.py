import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parent / ".env")

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
database_name = os.getenv("DATABASE_NAME", "smartserve")
client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
database = client[database_name]


def check_database_connection():
    client.admin.command("ping")
