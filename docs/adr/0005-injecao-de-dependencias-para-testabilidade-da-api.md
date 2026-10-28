# ADR 0005: Injeção de Dependências (`Depends`) para Isolamento de Testes

* **Status:** Aceito
* **Data:** 2026-10-26
* **Contexto:** Versão 2 (API & Arquitetura de Testes)

---

## 1. Contexto e Problema

Uma das regras inegociáveis de arquitetura deste projeto é o **isolamento total da suíte de testes automatizados**:
* A execução de `pytest` **NUNCA** deve depender do contêiner do MongoDB estar rodando ou de arquivos `.joblib` em disco.
* Se os endpoints da API instanciarem o repositório (`ReviewRepository()`) ou o serviço (`Classificador()`) diretamente dentro do escopo da função, torna-se impossível testar as rotas HTTP sem subir o banco de dados.

---

## 2. Decisão

1. **Adotar o sistema nativo de Injeção de Dependências do FastAPI (`Depends`):**
   * Criar provedores em `src/api/dependencias.py` para injetar instâncias de `ReviewRepository` e `Classificador`.
   * As funções de rota recebem essas instâncias como parâmetros injetados.
2. **Substituição nos Testes com `app.dependency_overrides`:**
   * Na suíte de testes (`tests/test_api.py`), substituir os provedores reais por implementações falsas em memória (*FakeReviewRepository* e *FakeClassificador*).

---

## 3. Alternativas Consideradas

* **Instanciação direta dentro das rotas:**
  * *Prós:* Menos linhas de código inicial.
  * *Contras:* Acoplamento rígido; testes teriam que usar `unittest.mock.patch` complexos ou depender de contêineres Docker ativos, violando a política de CI/CD.
* **Bibliotecas de DI externas (como `dependency-injector` ou `injector`):**
  * *Prós:* Padrão enterprise com contêineres de inversão de controle avançados.
  * *Contras:* Complexidade desnecessária (*over-engineering*) frente ao mecanismo nativo de `Depends` do FastAPI.

---

## 4. Consequências e Trade-offs

* **Positivas:**
  * Desacoplamento entre o ciclo de vida dos serviços e a camada de transporte HTTP.
  * Testes de integração de endpoints ultrarrápidos (< 1 segundo), 100% determinísticos e independentes de infraestrutura.
  * Facilidade de substituição de componentes no futuro (ex.: trocar o repositório ou versão do modelo).
* **Negativas / Riscos Mitigados:**
  * Curva de aprendizado mínima para novos desenvolvedores entenderem a mecânica do `Depends` e o gerenciador de contexto do FastAPI.
