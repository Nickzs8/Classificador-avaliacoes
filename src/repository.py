from pymongo import ASCENDING, MongoClient
from config import MONGO_COLLECTION, MONGO_DB, MONGO_URI

class ReviewRepository:

    def __init__(self, uri=MONGO_URI, db_name=MONGO_DB, collection_name=MONGO_COLLECTION):
        self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self._col = self._client[db_name][collection_name]

    # permite usar "with ReviewRepository() as repo:"
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.fechar()

    def fechar(self):
        self._client.close()

    def limpar(self):
        self._col.drop()

    """insere em lotes"""
    def inserir_varios(self, documentos, lote=5000):
        total = 0
        for i in range(0, len(documentos), lote):
            resultado = self._col.insert_many(documentos[i:i + lote], ordered=False)
            total += len(resultado.inserted_ids)
        return total

    def criar_indices(self):
        self._col.create_index([("rotulo", ASCENDING)])
        self._col.create_index([("produto", ASCENDING)])

    def contar(self, filtro=None):
        return self._col.count_documents(filtro or {})

    def contar_por_rotulo(self):
        pipeline = [
            {"$group": {"_id": "$rotulo", "total": {"$sum": 1}}},
            {"$sort": {"total": -1}},
        ]
        return {str(d["_id"]): d["total"] for d in self._col.aggregate(pipeline)}

    def buscar_rotulados(self):
        filtro = {"rotulo": {"$ne": None}}
        projecao = {"_id": 0, "texto": 1, "rotulo": 1}
        return list(self._col.find(filtro, projecao))