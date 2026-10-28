from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, DESCENDING, MongoClient, UpdateOne
from pymongo.errors import PyMongoError

from config import MONGO_COLLECTION, MONGO_DB, MONGO_URI

SENTIMENT_STAGE = {
    "$addFields": {
        "sentiment": {"$ifNull": ["$label", "$prediction.sentiment"]}
    }
}


class ReviewRepository:
    """Sole data access point for MongoDB analytical storage and review persistence."""

    def __init__(self, uri: str = MONGO_URI, db_name: str = MONGO_DB, collection_name: str = MONGO_COLLECTION):
        self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self._col = self._client[db_name][collection_name]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        """Closes the underlying MongoClient connection."""
        self._client.close()

    def clear(self):
        """Drops the reviews collection."""
        self._col.drop()

    def insert_many(self, documents: list[dict], batch_size: int = 5000) -> int:
        """Inserts documents in batches."""
        total = 0
        for i in range(0, len(documents), batch_size):
            result = self._col.insert_many(documents[i : i + batch_size], ordered=False)
            total += len(result.inserted_ids)
        return total

    def create_indexes(self):
        """Creates indexes for efficient querying and sorting."""
        self._col.create_index([("label", ASCENDING)])
        self._col.create_index([("product", ASCENDING)])
        self._col.create_index([("date", DESCENDING)])

    def count(self, filter_query: dict | None = None) -> int:
        """Counts documents matching filter criteria."""
        return self._col.count_documents(filter_query or {})

    def count_by_label(self) -> dict[str, int]:
        """Counts documents grouped by label."""
        pipeline = [
            {"$group": {"_id": "$label", "total": {"$sum": 1}}},
            {"$sort": {"total": -1}},
        ]
        return {str(d["_id"]): d["total"] for d in self._col.aggregate(pipeline)}

    def find_labeled(self) -> list[dict]:
        """Retrieves all labeled documents for model training."""
        filter_query = {"label": {"$ne": None}}
        projection = {"_id": 0, "text": 1, "label": 1}
        return list(self._col.find(filter_query, projection))

    def find_unlabeled(self) -> list[dict]:
        """Retrieves documents without a label and without a prediction."""
        filter_query = {"label": None, "prediction": None}
        projection = {"text": 1, "true_label": 1}
        return list(self._col.find(filter_query, projection))

    def save_predictions(self, predictions: list[dict], batch_size: int = 5000) -> int:
        """Performs bulk update to record prediction subdocuments."""
        operations = [
            UpdateOne(
                {"_id": p["_id"]},
                {"$set": {"prediction": p["prediction"]}},
            )
            for p in predictions
        ]
        modified = 0
        for i in range(0, len(operations), batch_size):
            result = self._col.bulk_write(operations[i : i + batch_size], ordered=False)
            modified += result.modified_count
        return modified

    def negative_reviews_by_product(self, limit: int = 10) -> list[dict]:
        """Calculates products with the highest volume of negative reviews."""
        pipeline = [
            SENTIMENT_STAGE,
            {"$match": {"sentiment": {"$ne": None}, "product": {"$ne": None}}},
            {
                "$group": {
                    "_id": "$product",
                    "total": {"$sum": 1},
                    "negatives": {
                        "$sum": {"$cond": [{"$eq": ["$sentiment", "negative"]}, 1, 0]}
                    },
                }
            },
            {"$match": {"negatives": {"$gt": 0}}},
            {"$sort": {"negatives": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "product": "$_id",
                    "negatives": 1,
                    "total": 1,
                    "pct_negatives": {
                        "$round": [
                            {"$multiply": [{"$divide": ["$negatives", "$total"]}, 100]},
                            1,
                        ]
                    },
                }
            },
        ]
        return list(self._col.aggregate(pipeline))

    def monthly_evolution(self) -> list[dict]:
        """Aggregates review volume per month and sentiment."""
        pipeline = [
            SENTIMENT_STAGE,
            {"$match": {"date": {"$ne": None}, "sentiment": {"$ne": None}}},
            {
                "$group": {
                    "_id": {
                        "month": {"$dateToString": {"format": "%Y-%m", "date": "$date"}},
                        "sentiment": "$sentiment",
                    },
                    "total": {"$sum": 1},
                }
            },
            {"$sort": {"_id.month": 1, "_id.sentiment": 1}},
            {
                "$project": {
                    "_id": 0,
                    "month": "$_id.month",
                    "sentiment": "$_id.sentiment",
                    "total": 1,
                }
            },
        ]
        return list(self._col.aggregate(pipeline))

    def average_confidence_by_class(self) -> list[dict]:
        """Calculates average model prediction confidence per predicted sentiment class."""
        pipeline = [
            {"$match": {"prediction": {"$ne": None}}},
            {
                "$group": {
                    "_id": "$prediction.sentiment",
                    "total": {"$sum": 1},
                    "average_confidence": {"$avg": "$prediction.confidence"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "class": "$_id",
                    "total": 1,
                    "average_confidence": {"$round": ["$average_confidence", 3]},
                }
            },
            {"$sort": {"class": 1}},
        ]
        return list(self._col.aggregate(pipeline))

    def accuracy_rate(self) -> list[dict]:
        """Calculates accuracy percentage against true labels for predicted reviews."""
        pipeline = [
            {"$match": {"prediction": {"$ne": None}, "true_label": {"$ne": None}}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "hits": {
                        "$sum": {
                            "$cond": [{"$eq": ["$prediction.sentiment", "$true_label"]}, 1, 0]
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total": 1,
                    "hits": 1,
                    "accuracy_rate": {
                        "$round": [
                            {"$multiply": [{"$divide": ["$hits", "$total"]}, 100]},
                            1,
                        ]
                    },
                }
            },
        ]
        return list(self._col.aggregate(pipeline))

    def ping(self) -> bool:
        """Checks whether MongoDB is alive and reachable."""
        try:
            self._client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    def insert_review(self, doc: dict) -> str:
        """Inserts a single review document and returns its string ID."""
        result = self._col.insert_one(doc)
        return str(result.inserted_id)

    def find_by_id(self, review_id: str) -> dict | None:
        """Finds review by ID or returns None if invalid/absent."""
        try:
            object_id = ObjectId(review_id)
        except InvalidId:
            return None
        doc = self._col.find_one({"_id": object_id})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def list_recent(self, limit: int = 10) -> list[dict]:
        """Lists recent reviews sorted by date descending."""
        cursor = (
            self._col.find()
            .sort([("date", DESCENDING)])
            .limit(limit)
        )
        documents = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(doc)
        return documents
