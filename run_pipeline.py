"""
Script de orquestração da esteira de Machine Learning (V1 Batch).

Executa em sequência as etapas de inicialização e treino do projeto:
1. src/prepare_data.py - Limpeza, regras de negócio e rotulagem a partir do CSV bruto.
2. src/ingest.py       - Ingestão BSON e criação de índices no MongoDB (requer Docker ativo).
3. src/train.py        - Treinamento do classificador TF-IDF + Regressão Logística e exportação do .joblib.
"""

import subprocess
import sys
import time
from pathlib import Path


def verificar_mongodb_ativo() -> bool:
    """Verifica se o contêiner do MongoDB está ativo via Docker Compose antes das etapas de banco."""
    print(f"\n{'='*70}")
    print("[INFO] Verificando status do MongoDB via Docker Compose...")
    print(f"{'='*70}")

    try:
        res = subprocess.run(
            ["docker", "compose", "ps", "--status", "running", "-q"],
            capture_output=True,
            text=True,
            check=False,
        )

        if res.returncode == 0 and res.stdout.strip():
            print("[OK] Contêiner do MongoDB ativo e em execução.")
            return True

        print("[ERRO] O contêiner do MongoDB não está em execução.")
        print("Inicie o banco de dados antes de executar o pipeline com:")
        print("       docker compose up -d")
        return False

    except FileNotFoundError:
        print("\n[ERRO] O comando 'docker' não foi encontrado no PATH do sistema.")
        print("Certifique-se de que o Docker está instalado e acessível.")
        return False
    except Exception as e:
        print(f"\n[ERRO] Falha inesperada ao verificar o Docker: {e}")
        return False


ETAPAS = [
    {
        "nome": "1/3: Preparação dos Dados",
        "script": "src/prepare_data.py",
        "descricao": "Lê data/raw/B2W-Reviews01.csv, limpa, rotula e gera data/reviews.csv",
        "requer_docker": False,
    },
    {
        "nome": "2/3: Ingestão no MongoDB",
        "script": "src/ingest.py",
        "descricao": "Carrega data/reviews.csv, converte em BSON e insere na coleção do MongoDB",
        "requer_docker": True,
    },
    {
        "nome": "3/3: Treinamento do Modelo",
        "script": "src/train.py",
        "descricao": "Treina o classificador (TF-IDF + LogisticRegression) e salva o modelo .joblib",
        "requer_docker": True,
    },
]


def executar_etapa(etapa: dict) -> bool:
    script_path = Path(etapa["script"])
    if not script_path.exists():
        print(f"\n[ERRO] Script não encontrado: {script_path}")
        return False

    if etapa.get("requer_docker"):
        if not verificar_mongodb_ativo():
            print(f"\n[ERRO] Não foi possível validar o MongoDB para a etapa '{etapa['nome']}'.")
            return False

    print(f"\n{'='*70}")
    print(f"[ETAPA {etapa['nome']}]")
    print(f"Descrição: {etapa['descricao']}")
    print(f"Comando:   {sys.executable} {etapa['script']}")
    print(f"{'='*70}\n")

    inicio = time.time()
    resultado = subprocess.run([sys.executable, str(script_path)])
    duracao = time.time() - inicio

    if resultado.returncode != 0:
        print(f"\n[ERRO] Etapa '{etapa['nome']}' finalizada com código de erro {resultado.returncode}.")
        if etapa.get("requer_docker"):
            print("[DICA] Se o erro for de conexão com o banco de dados, verifique:")
            print("       docker compose ps")
            print("       docker compose logs mongo")
        return False

    print(f"\n[OK] Concluído em {duracao:.2f}s")
    return True


def main():
    print("=" * 70)
    print("INICIALIZAÇÃO DA PIPELINE DE MACHINE LEARNING (V1 BATCH)")
    print("=" * 70)

    raw_csv = Path("data/raw/B2W-Reviews01.csv")
    reviews_csv = Path("data/reviews.csv")
    if not raw_csv.exists() and not reviews_csv.exists():
        print("\n[AVISO] Nenhum arquivo de dados encontrado em 'data/raw/' ou 'data/'.")
        print("Certifique-se de que 'data/raw/B2W-Reviews01.csv' ou 'data/reviews.csv' esteja presente.")
        sys.exit(1)

    inicio_total = time.time()

    for etapa in ETAPAS:
        sucesso = executar_etapa(etapa)
        if not sucesso:
            print("\n[ERRO] Pipeline interrompida devido a falha na etapa anterior.")
            sys.exit(1)

    tempo_total = time.time() - inicio_total
    print("\n" + "=" * 70)
    print(f"[CONCLUÍDO] Pipeline executada com sucesso em {tempo_total:.2f}s.")
    print("=" * 70)


if __name__ == "__main__":
    main()
