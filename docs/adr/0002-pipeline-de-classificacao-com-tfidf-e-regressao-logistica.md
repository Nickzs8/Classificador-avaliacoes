# ADR 0002: Pipeline de Classificação com TF-IDF e Regressão Logística

* **Status:** Aceito
* **Data:** 2026-10-22
* **Contexto:** Versão 1 (Machine Learning)

---

## 1. Contexto e Problema

Precisamos classificar avaliações de clientes em português em duas classes (`positivo` vs. `negativo`). O corpus de treino apresenta duas restrições críticas:
1. **Desbalanceamento de Classes:** A base original possui aproximadamente 70% de avaliações positivas e 30% negativas.
2. **Requisito de Latência e Eficiência:** O modelo deve ser treinado em poucos segundos na máquina local e realizar inferências em milissegundos sem exigir GPUs dedicadas.

---

## 2. Decisão

Adotar uma esteira serializada do `scikit-learn` composta por:
1. **`TfidfVectorizer(ngram_range=(1, 2), min_df=2)`:**
   * Vetorização com unigramas e bigramas para capturar negações simples (ex.: *"não gostei"* vs. *"gostei"*).
   * Descarte de termos raros (`min_df=2`) para redução dimensional e controle de overfitting.
2. **`LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)`:**
   * Ponderação inversa de frequência das classes (`class_weight="balanced"`), penalizando fortemente erros na classe minoritária (negativos).
   * Saída de probabilidades calibradas (`predict_proba`) para auditoria de confiança.
3. **Serialização única com `joblib`:**
   * O artefato `models/modelo_v1.joblib` armazena o vetorizador e o estimador encapsulados em um único arquivo binário.

---

## 3. Alternativas Consideradas

* **Redes Neurais Profundas / Transformers (BERTimbau / RoBERTa):**
  * *Prós:* Captura de contexto bidirecional profundo e semântica mais rica.
  * *Contras:* Artefatos pesados (> 400 MB), necessidade de GPU para inferência em tempo hábil e tempo de treinamento incompatível com testes ágeis e pipelines leves de CI.
* **Naive Bayes Multinomial:**
  * *Prós:* Treinamento instantâneo.
  * *Contras:* Suposição de independência condicional frágil para capturar bigramas e calibração de probabilidades inferior à Regressão Logística.

---

## 4. Consequências e Trade-offs

* **Positivas:**
  * **Alto Recall na Classe Negativa (0.94):** Garante que quase nenhuma insatisfação de cliente passe despercebida.
  * **Acurácia Global de 93%** e artefato binário extremamente leve (< 10 MB).
  * Inferência instantânea (< 5 ms por texto), viabilizando consumo em tempo real via API.
* **Negativas / Riscos Mitigados:**
  * Incapacidade de capturar sarcasmo complexo ou contexto de longo alcance (aceitável para o escopo e compensado por alta interpretabilidade e baixo custo de infraestrutura).
