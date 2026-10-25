from pymongo import ASCENDING, MongoClient, UpdateOne

from config import MONGO_COLLECTION, MONGO_DB, MONGO_URI

SENTIMENTO = {"$addFields": {"sentimento": {"$ifNull": ["$rotulo", "$predicao.classe"]}}}

class ReviewRepository:
    """Único ponto de acesso ao MongoDB no projeto."""

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

    def inserir_varios(self, documentos, lote=5000):
        """Insere em lotes."""
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

    def buscar_sem_predicao(self):
        """Documentos sem rótulo e ainda sem predição (o _id vem por padrão)."""
        filtro = {"rotulo": None, "predicao": None}
        projecao = {"texto": 1, "rotulo_real": 1}
        return list(self._col.find(filtro, projecao))

    def gravar_predicoes(self, predicoes, lote=5000):
        """predicoes: lista de dicts {"_id": ..., "predicao": {...}}."""
        operacoes = [
            UpdateOne({"_id": p["_id"]}, {"$set": {"predicao": p["predicao"]}})
            for p in predicoes
        ]
        modificados = 0
        for i in range(0, len(operacoes), lote):
            resultado = self._col.bulk_write(operacoes[i:i + lote], ordered=False)
            modificados += resultado.modified_count
        return modificados

    def negativas_por_produto(self, limite=10):
        ## produtos com mais avaliacoes negativas

        pipeline = [
            SENTIMENTO,
            {"$match": {"sentimento": {"$ne": None}, "produto": {"$ne": None}}},
            {
                "$group": {
                    "_id": "$produto",
                    "total": {"$sum": 1},
                    "negativas": {
                        "$sum": {"$cond": [{"$eq": ["$sentimento", "negativo"]}, 1, 0]}
                    },
                }
            },
            {"$match": {"negativas": {"$gt": 0}}},
            {"$sort": {"negativas": -1}},
            {"$limit": limite},
            {
                "$project": {
                    "_id": 0,
                    "produto": "$_id",
                    "negativas": 1,
                    "total": 1,
                    "pct_negativas": {
                        "$round": [
                            {"$multiply": [{"$divide": ["$negativas", "$total"]}, 100]},
                            1,
                        ]
                    },
                }
            },
        ]
        return list(self._col.aggregate(pipeline))

    def evolucao_por_mes(self):
        """Total de avaliações por mês e sentimento (ignora datas nulas)."""
        pipeline = [
            SENTIMENTO,
            {"$match": {"data": {"$ne": None}, "sentimento": {"$ne": None}}},
            {
                "$group": {
                    "_id": {
                        "mes": {"$dateToString": {"format": "%Y-%m", "date": "$data"}},
                        "sentimento": "$sentimento",
                    },
                    "total": {"$sum": 1},
                }
            },
            {"$sort": {"_id.mes": 1, "_id.sentimento": 1}},
            {
                "$project": {
                    "_id": 0,
                    "mes": "$_id.mes",
                    "sentimento": "$_id.sentimento",
                    "total": 1,
                }
            },
        ]
        return list(self._col.aggregate(pipeline))

    def confianca_media_por_classe(self):
        """Confiança média das predições, por classe prevista."""
        pipeline = [
            {"$match": {"predicao": {"$ne": None}}},
            {
                "$group": {
                    "_id": "$predicao.classe",
                    "total": {"$sum": 1},
                    "confianca_media": {"$avg": "$predicao.confianca"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "classe": "$_id",
                    "total": 1,
                    "confianca_media": {"$round": ["$confianca_media", 3]},
                }
            },
            {"$sort": {"classe": 1}},
        ]
        return list(self._col.aggregate(pipeline))

    def taxa_acerto(self):
        """% de predições iguais ao rotulo_real, entre os documentos com predição."""
        pipeline = [
            {"$match": {"predicao": {"$ne": None}}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "acertos": {
                        "$sum": {"$cond": [{"$eq": ["$predicao.classe", "$rotulo_real"]}, 1, 0]}
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total": 1,
                    "acertos": 1,
                    "taxa_acerto": {
                        "$round": [
                            {"$multiply": [{"$divide": ["$acertos", "$total"]}, 100]},
                            1,
                        ]
                    },
                }
            },
        ]
        return list(self._col.aggregate(pipeline))