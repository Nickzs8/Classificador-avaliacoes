#!/usr/bin/env bash
set -e

REPO="Nickzs8/Classificador-avaliacoes"

echo "=== Criando issues da V2 no repositório: $REPO ==="

gh issue create --repo "$REPO" \
  --title "[V2] Etapa 1: Contrato e Planejamento da API" \
  --body "## Objetivo
Fechar contratos de dados, endpoints, limites de tamanho e preparar o repositório para o desenvolvimento da V2.

## Tarefas
- [ ] Criar a branch \`v2\` (\`git checkout -b v2\`)
- [ ] Definir schemas de entrada e saída
- [ ] Documentar o contrato no README e no ROADMAP_V2
- [ ] Definir limites: texto entre 3 e 2000 caracteres, produto opcional"

gh issue create --repo "$REPO" \
  --title "[V2] Etapa 2: Preparação do Projeto e Extensão do Repositório" \
  --body "## Objetivo
Adicionar dependências necessárias e estender o \`ReviewRepository\` com os métodos exigidos pela API.

## Tarefas
- [ ] Instalar e fixar no \`requirements.txt\`: \`fastapi\`, \`uvicorn[standard]\`, \`httpx\`
- [ ] Criar as pastas \`src/api/\` e \`src/interface/\`
- [ ] Acrescentar métodos ao \`ReviewRepository\`:
  - \`inserir_avaliacao(doc)\`
  - \`buscar_por_id(id)\`
  - \`listar_recentes(limite=10)\`
  - \`ping()\` (para o healthcheck)
  - Criar índice no campo \`data\`
- [ ] Ajustar agregação de \`taxa_acerto\` para ignorar documentos com \`rotulo_real: null\`
- [ ] Atualizar \`.env.example\` com \`API_HOST\` e \`API_PORT\`"

gh issue create --repo "$REPO" \
  --title "[V2] Etapa 3: Serviço Compartilhado de Classificação (classificador.py)" \
  --body "## Objetivo
Isolar a inferência em uma camada de serviço (*Service Layer*) reutilizável tanto pelo batch quanto pela API.

## Tarefas
- [ ] Criar \`src/classificador.py\` com a classe \`Classificador\`
- [ ] Implementar carregamento único do modelo \`.joblib\` na inicialização
- [ ] Mover lógica de montagem do payload de predição do \`predict.py\` para o serviço
- [ ] Refatorar \`src/predict.py\` para consumir o \`Classificador\`
- [ ] Lançar exceção clara caso o arquivo do modelo não exista
- [ ] Criar testes unitários em \`tests/test_classificador.py\`"

gh issue create --repo "$REPO" \
  --title "[V2] Etapa 4: Implementação dos Endpoints FastAPI e Schemas Pydantic" \
  --body "## Objetivo
Desenvolver a API REST com FastAPI respeitando contratos, injeção de dependência e rotas síncronas.

## Tarefas
- [ ] Implementar \`src/api/schemas.py\` (\`AvaliacaoEntrada\` e \`AvaliacaoSaida\`)
- [ ] Implementar \`src/api/dependencias.py\` (\`Depends\` para repositório e classificador)
- [ ] Implementar \`src/api/main.py\` com as rotas:
  - \`POST /avaliacoes\` (201 Created)
  - \`GET /avaliacoes/{id}\` (200 OK / 404 Not Found)
  - \`GET /avaliacoes?limite=10\` (200 OK)
  - \`GET /saude\` (200 OK / 503 Service Unavailable)
- [ ] Usar \`def\` nas rotas para execução em threadpool
- [ ] Validar documentação interativa em \`/docs\`"

gh issue create --repo "$REPO" \
  --title "[V2] Etapa 5: Testes Automatizados da API (TestClient e Mocks)" \
  --body "## Objetivo
Garantir cobertura total dos endpoints sem depender de conexão com o MongoDB.

## Tarefas
- [ ] Criar \`tests/test_api.py\` usando \`TestClient\` do FastAPI
- [ ] Implementar repositório mock em memória usando \`app.dependency_overrides\`
- [ ] Testar cenários:
  - \`POST\` válido retorna 201 e salva com \`origem: 'api'\` e \`rotulo: null\`
  - Validação de entrada: texto < 3 caracteres ou vazio (422)
  - Validação de entrada: texto > 2000 caracteres (422)
  - \`GET\` com ID inexistente (404)
  - \`GET /avaliacoes\` com paginação/limite
  - \`GET /saude\` com sucesso e simulação de falha (503)"

gh issue create --repo "$REPO" \
  --title "[V2] Etapa 6: Interface de Envio e Resultado em Tempo Real" \
  --body "## Objetivo
Criar interface para o usuário final submeter avaliações e receber a classificação em tempo real.

## Tarefas
- [ ] Implementar interface (Streamlit) consumindo a API via \`httpx\`
- [ ] Formulário com campo de texto da avaliação e produto opcional
- [ ] Botão de submissão conectado ao \`POST /avaliacoes\`
- [ ] Exibição visual do resultado: sentimento predito e barra de confiança"

gh issue create --repo "$REPO" \
  --title "[V2] Etapa 7: Histórico de Avaliações e Tratamento de Erros" \
  --body "## Objetivo
Aprimorar a experiência do usuário com histórico dinâmico e tratamento de indisponibilidade.

## Tarefas
- [ ] Exibir histórico recente consumindo \`GET /avaliacoes\`
- [ ] Tratamento amigável de erro se a API ou banco estiverem fora do ar
- [ ] Alerta visual quando a confiança da predição for baixa (< 60%)
- [ ] Feedback visual de carregamento durante a inferência"

gh issue create --repo "$REPO" \
  --title "[V2] Etapa 8: Documentação Final, Exemplos e Release v2.0" \
  --body "## Objetivo
Finalizar a documentação, atualizar guias de execução e gerar a tag de release v2.0.

## Tarefas
- [ ] Atualizar \`README.md\` e \`README.pt-br.md\` com seção dedicada à V2
- [ ] Exemplos práticos de consumo da API via \`curl\` e documentação OpenAPI
- [ ] Validar execução limpa do zero
- [ ] Realizar merge da branch \`v2\` e criar a tag \`v2.0\`"

echo "=== Todas as issues foram criadas com sucesso! ==="
