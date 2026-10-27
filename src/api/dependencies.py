from functools import lru_cache
from typing import Generator
from repository import ReviewRepository
from services.classificador import Classificador


def get_repositorio() -> Generator[ReviewRepository, None, None]:
    """Injeta o repositório e garante o fechamento da conexão ao final da requisição."""

    with ReviewRepository() as repo:
        yield repo


@lru_cache(maxsize=1)
def get_classificador() -> Classificador:
    """Instancia o modelo .joblib uma única vez na memória."""

    return Classificador()
