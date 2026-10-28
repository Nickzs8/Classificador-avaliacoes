from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_repositorio, get_classificador


class FakeReviewRepository:
    """Implementação falsa em memória do ReviewRepository para isolamento dos testes."""

    def __init__(self):
        self.documentos = []
        self._ping_ok = True

    def ping(self) -> bool:
        return self._ping_ok

    def inserir_avaliacao(self, doc: dict) -> str:
        doc_copia = dict(doc)
        id_gerado = f"6720c1f2e4b0a1d2c3e4f5a{len(self.documentos) + 1}"
        doc_copia["_id"] = id_gerado
        self.documentos.append(doc_copia)
        return id_gerado

    def buscar_por_id(self, id_avaliacao: str) -> dict | None:
        for doc in self.documentos:
            if doc["_id"] == id_avaliacao:
                return dict(doc)
        return None

    def listar_recentes(self, limite: int = 10) -> list[dict]:
        # Retorna os últimos inseridos (ordem cronológica decrescente)
        return [dict(d) for d in reversed(self.documentos)][:limite]


class FakeClassificador:
    """Implementação falsa em memória do Classificador sem carregar .joblib."""

    def __init__(self, modelo_ok: bool = True):
        self.modelo = object() if modelo_ok else None
        self.versao = "modelo_teste"

    def classificar_texto(self, texto: str) -> dict:
        classe = "positivo" if "bom" in texto.lower() or "excelente" in texto.lower() else "negativo"
        return {
            "classe": classe,
            "confianca": 0.95,
            "modelo": self.versao,
            "data": datetime.now(timezone.utc),
        }


@pytest.fixture
def fake_repo():
    return FakeReviewRepository()


@pytest.fixture
def fake_classificador():
    return FakeClassificador()


@pytest.fixture
def cliente(fake_repo, fake_classificador):
    """TestClient com dependências do banco e classificador substituídas em memória."""
    app.dependency_overrides[get_repositorio] = lambda: fake_repo
    app.dependency_overrides[get_classificador] = lambda: fake_classificador

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


## testes de criação e persistencia

def test_post_avaliacao_valida_retorna_201_e_grava_esquema_correto(cliente, fake_repo):
    payload = {
        "texto": "Produto excelente, chegou muito rápido!",
        "produto": "Fone Bluetooth X",
    }
    response = cliente.post("/avaliacoes", json=payload)

    assert response.status_code == 201
    dados = response.json()

    assert dados["id"].startswith("6720c1f2e4b0a1d2c3e4f5a")
    assert dados["texto"] == "Produto excelente, chegou muito rápido!"
    assert dados["produto"] == "Fone Bluetooth X"
    assert dados["classe"] == "positivo"
    assert dados["confianca"] == 0.95
    assert dados["modelo"] == "modelo_teste"
    assert "data" in dados

    # Validação do documento persistido no repositório
    assert len(fake_repo.documentos) == 1
    doc_salvo = fake_repo.documentos[0]
    assert doc_salvo["origem"] == "api"
    assert doc_salvo["nota"] is None
    assert doc_salvo["rotulo"] is None
    assert doc_salvo["rotulo_real"] is None
    assert doc_salvo["predicao"]["classe"] == "positivo"


def test_post_avaliacao_texto_menor_que_3_retorna_422(cliente):
    response = cliente.post("/avaliacoes", json={"texto": "Oi"})
    assert response.status_code == 422
    assert any(erro["type"] == "string_too_short" for erro in response.json()["detail"])


def test_post_avaliacao_texto_vazio_ou_apenas_espacos_retorna_422(cliente):
    # Texto em branco interceptado pelo @field_validator
    response = cliente.post("/avaliacoes", json={"texto": "     "})
    assert response.status_code == 422

    # String vazia
    response_vazio = cliente.post("/avaliacoes", json={"texto": ""})
    assert response_vazio.status_code == 422


def test_post_avaliacao_texto_maior_que_2000_retorna_422(cliente):
    texto_gigante = "a" * 2001
    response = cliente.post("/avaliacoes", json={"texto": texto_gigante})
    assert response.status_code == 422
    assert any(erro["type"] == "string_too_long" for erro in response.json()["detail"])


# testes de consulta

def test_get_avaliacao_por_id_existente_retorna_200(cliente):
    # 1 Cria a avaliação
    post_res = cliente.post("/avaliacoes", json={"texto": "Muito bom produto!"})
    id_gerado = post_res.json()["id"]

    # 2 Busca pelo ID
    get_res = cliente.get(f"/avaliacoes/{id_gerado}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == id_gerado
    assert get_res.json()["texto"] == "Muito bom produto!"


def test_get_avaliacao_por_id_inexistente_retorna_404(cliente):
    response = cliente.get("/avaliacoes/id_inexistente_123")
    assert response.status_code == 404
    assert "não foi encontrada" in response.json()["detail"]


# testes de listagem

def test_get_avaliacoes_com_limite_e_paginacao(cliente):
    # Cadastra 5 avaliações
    for i in range(5):
        cliente.post("/avaliacoes", json={"texto": f"Avaliação teste número {i+1}"})

    # Consulta com limite de 3
    response = cliente.get("/avaliacoes?limite=3")
    assert response.status_code == 200
    dados = response.json()
    assert len(dados) == 3
    # A primeira retornada deve ser a mais recente (número 5)
    assert dados[0]["texto"] == "Avaliação teste número 5"


def test_get_avaliacoes_limite_invalido_retorna_422(cliente):
    # Limite menor que 1
    res_zero = cliente.get("/avaliacoes?limite=0")
    assert res_zero.status_code == 422

    # Limite maior que 100
    res_grande = cliente.get("/avaliacoes?limite=101")
    assert res_grande.status_code == 422


# testes de saude

def test_get_saude_sucesso_retorna_200(cliente):
    response = cliente.get("/saude")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "banco": True, "modelo": True}


def test_get_saude_falha_no_banco_retorna_503(cliente, fake_repo):
    fake_repo._ping_ok = False  # Simula queda de conexão do MongoDB
    response = cliente.get("/saude")

    assert response.status_code == 503
    assert response.json() == {"status": "erro", "banco": False, "modelo": True}


def test_get_saude_falha_no_modelo_retorna_503(cliente, fake_classificador):
    fake_classificador.modelo = None  # Simula modelo não carregado
    response = cliente.get("/saude")

    assert response.status_code == 503
    assert response.json() == {"status": "erro", "banco": True, "modelo": False}
