# ADR 0002: Classification Pipeline with TF-IDF and Logistic Regression

* **Status:** Accepted
* **Date:** 2026-10-22
* **Context:** Version 1 (Machine Learning)

---

## 1. Context and Problem Statement

The system must classify Portuguese customer reviews into binary sentiments (`positivo` vs. `negativo`). The training dataset presents two critical engineering constraints:
1. **Class Imbalance:** The raw dataset comprises approximately 70% positive and 30% negative reviews.
2. **Latency and Resource Constraints:** The model must train within seconds on a standard developer machine and perform real-time inference in low single-digit milliseconds without dedicated GPU hardware.

---

## 2. Decision

Adopt a serialized Scikit-Learn pipeline consisting of:
1. **`TfidfVectorizer(ngram_range=(1, 2), min_df=2)`:**
   * Unigram and bigram extraction to capture basic negation patterns (e.g., *"não gostei"* vs. *"gostei"*).
   * Pruning infrequent terms (`min_df=2`) for dimensionality reduction and overfitting mitigation.
2. **`LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)`:**
   * Inversely weighted class penalties (`class_weight="balanced"`) to penalize misclassifications on the minority class (negatives).
   * Well-calibrated probability outputs (`predict_proba`) for prediction confidence scoring.
3. **Unified Serialization via `joblib`:**
   * The artifact `models/modelo_v1.joblib` packages both the vectorizer vocabulary and classifier coefficients into a single, self-contained binary file.

---

## 3. Considered Alternatives

* **Deep Neural Networks / Transformers (BERTimbau / RoBERTa):**
  * *Pros:* Rich semantic understanding and bidirectional context capture.
  * *Cons:* Large artifact size (> 400 MB), high memory consumption, requiring GPU instances for acceptable inference latency, and training times incompatible with rapid local CI/CD feedback loops.
* **Multinomial Naive Bayes:**
  * *Pros:* Near-instantaneous training.
  * *Cons:* Conditional independence assumption struggles with bigram phrases, and posterior probabilities tend to be poorly calibrated compared to Logistic Regression.

---

## 4. Consequences and Trade-offs

* **Positive:**
  * Fast training: completes in ~5 seconds on 18,000 training samples.
  * Ultra-low inference latency: < 5 ms per request in production.
  * High recall on negative reviews (0.94), ensuring customer dissatisfaction is reliably detected.
  * Small disk footprint: model artifact is only ~1.1 MB.
* **Negative / Mitigated Risks:**
  * Linear models cannot detect complex linguistic nuances like heavy sarcasm or multi-sentence conditional reasoning.
