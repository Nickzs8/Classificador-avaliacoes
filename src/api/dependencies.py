from functools import lru_cache
from typing import Generator
from repository import ReviewRepository
from services.classifier import Classifier


def get_repository() -> Generator[ReviewRepository, None, None]:
    """Injects repository and guarantees connection teardown after request."""
    with ReviewRepository() as repo:
        yield repo


@lru_cache(maxsize=1)
def get_classifier() -> Classifier:
    """Instantiates the .joblib model once in memory."""
    return Classifier()
