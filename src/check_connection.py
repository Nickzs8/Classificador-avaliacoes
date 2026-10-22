from pymongo import MongoClient
from pymongo.errors import PyMongoError

from config import MONGO_URI, MONGO_DB, MONGO_COLLECTION


def main():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        print("✔ Conexão com o MongoDB OK")

        col = client[MONGO_DB][MONGO_COLLECTION + "_teste"]
        res = col.insert_one({"texto": "teste de conexão"})
        doc = col.find_one({"_id": res.inserted_id})
        print("✔ Documento gravado e lido:", doc)

        col.drop()
        print("✔ Coleção de teste removida")
    except PyMongoError as e:
        print("✘ Falha na conexão:", e)
    finally:
        client.close()


if __name__ == "__main__":
    main()