<div align="center">

# RAQIB
### Fraud Scoring, Engineered with Care

**From a notebook with a silent bug to a tested, containerized AI service.**

A software engineering journey through **SDAIA Academy · SDA-AIE-113**

[![CI](https://github.com/jnjnmaizi/JanaAlhuamizi_SDA-AIE-113_WorkShop/actions/workflows/ci.yml/badge.svg)](https://github.com/jnjnmaizi/JanaAlhuamizi_SDA-AIE-113_WorkShop/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12-DB2777?style=flat-square)
![FastAPI](https://img.shields.io/badge/API-FastAPI-F9A8D4?style=flat-square&labelColor=831843)
![Pytest](https://img.shields.io/badge/Tests-Pytest-DB2777?style=flat-square)
![Docker](https://img.shields.io/badge/Runtime-Docker-F9A8D4?style=flat-square&labelColor=831843)

**[Architecture](#02--how-raqib-works) · [The labs](#03--the-workshop-journey) · [Quick start](#04--quick-start)**

</div>

---

## 01 · The Idea

A machine learning model is only one part of an AI system.

The harder question is: **Can we trust the software around it?**

**Raqib** is a workshop fraud-scoring service. It receives a transaction, checks the data, asks a trained scikit-learn model for a risk score, and uses clear rules to decide whether to **allow**, **review**, or **block** the transaction.

The project began with legacy notebook code that could run **without an error but still produce wrong results**. Each lab added another layer of reliability.

> **My approach:** Don't just make it work. Understand it, test what could fail, and make the result easy to explain.

| Input | Inside the service | Output |
| :--- | :--- | :--- |
| Transaction JSON | Validation → feature extraction → model → decision policy | Risk probability, decision, model version, trace ID |
| Invalid request | Strict field checks | Safe, understandable error |
| Missing model file | Startup validation | Clear failure before serving requests |

*This is an educational workshop service, not a live payment system. A model score is a risk signal, not proof of fraud.*

## 02 · How Raqib Works

### One transaction, step by step

~~~mermaid
flowchart TD
    A["Transaction JSON"] --> B["FastAPI<br/>Validate request"]
    B --> C["Domain<br/>Build model features"]
    C --> D["FraudScorer<br/>Coordinate scoring"]
    D --> E["SklearnModel adapter<br/>Run trained model"]
    E --> F["Fraud probability"]
    F --> G{"Decision policy"}
    G -->|"Lower risk"| H["ALLOW"]
    G -->|"Review band"| I["REVIEW"]
    G -->|"Block threshold reached"| J["BLOCK"]
    H --> K["Response + trace ID"]
    I --> K
    J --> K
    classDef pink fill:#FCE7F3,stroke:#BE185D,color:#500724;
    classDef pale fill:#FFF1F2,stroke:#DB2777,color:#500724;
    class B,C,D,E,F,G pink;
    class A,H,I,J,K pale;
~~~

### Why the layers are separate

| Layer | What it does | Where to find it |
| :--- | :--- | :--- |
| **Domain** | Defines transactions, features, and business decisions. | `src/fraud_service/domain/` |
| **Service** | Connects the model's prediction to the decision rule. | `service/scorer.py` and `service/interfaces.py` |
| **Adapter** | Translates features into the trained scikit-learn pipeline's format. | `adapters/sklearn_model.py` |
| **API** | Checks HTTP requests and returns useful, consistent responses. | `src/fraud_service/api/` |
| **Configuration** | Validates settings before the API starts. | `config.py` |
| **Logging** | Produces searchable JSON events and masks sensitive keys. | `logging_setup.py` |

**The benefit:** changing the API should not change the decision rules. Changing the ML library should not require rewriting the domain.

### The decision rule

The default block threshold is **0.85** and the review band is **0.15** below it.

| Probability | Decision |
| :--- | :--- |
| Less than **0.70** | `allow` |
| **0.70** to less than **0.85** | `review` |
| **0.85** or higher | `block` |

These values reflect the implementation in [`domain/policies.py`](src/fraud_service/domain/policies.py); they are not a claim about real-world model accuracy.

## 03 · The Workshop Journey

**Seven modules, one evolving project.** Every lab answers one practical engineering question.

| Lab | The question | What I implemented |
| :--- | :--- | :--- |
| **01 · Refactoring** | How do I catch a silent bug? | Clean domain/service/adapter layers, a batch entrypoint, and comparison with trusted golden scores. |
| **02a · Prediction API** | How can another app call the model? | FastAPI, strict request schemas, prediction and service health endpoints. |
| **02b · API Hardening** | What if the request is invalid or traffic grows? | Model warm-up, safe error responses, trace IDs, and load tests. |
| **03 · Docker** | Will it run consistently elsewhere? | Multi-stage image, non-root user, health checks, and a Docker Compose stack. |
| **04 · Testing** | How do I prevent a regression? | Unit, integration, and behavioural tests, malformed-request checks, golden-file testing, and coverage. |
| **05 · CI/CD** | Can the checks run automatically? | GitHub Actions for lint, tests, Docker smoke tests, publishing, and nightly regression testing. |
| **06 · Security** | How can I investigate issues safely? | Typed settings, fail-fast startup, structured JSON logging, secret masking, and an incident-response drill. |

**Workshop reference:** [Original lab instructions](https://github.com/snow10100/fraud-service/tree/main/labs).

## 04 · Quick Start

### Requirements

- Python **3.12** and Git
- Docker Desktop, only if using the container option
- The bundled model at `models/fraud_xgb_v3.joblib`

### Option A: Run locally with Python

**1. Clone and install.**

~~~bash
git clone https://github.com/jnjnmaizi/JanaAlhuamizi_SDA-AIE-113_WorkShop.git
cd JanaAlhuamizi_SDA-AIE-113_WorkShop
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
~~~

On Windows, activate with `.venv\Scripts\activate`.

**2. Create a local `.env` file in the repository root.**

~~~dotenv
FRAUD_MODEL_PATH=models/fraud_xgb_v3.joblib
FRAUD_BLOCK_THRESHOLD=0.85
FRAUD_LOG_LEVEL=INFO
~~~

See [`configs/settings.example.env`](configs/settings.example.env) for the documented settings. **Never commit real secrets or your local `.env`.**

**3. Start the API.**

~~~bash
python -m uvicorn fraud_service.api.app:create_app --factory --reload
~~~

Open **http://localhost:8000/docs** for interactive API documentation.

### Option B: Run with Docker

~~~bash
docker compose up --build -d
docker compose ps
~~~

The Compose stack includes the fraud API and a Redis service, both with health checks. To stop it:

~~~bash
docker compose down
~~~

### Try a prediction

With the API running, open a second terminal:

~~~bash
curl -X POST http://localhost:8000/v1/predict \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: jana-demo-001" \
  -d @payloads/sample.json
~~~

The supplied sample input is:

~~~json
{
  "transaction_id": "TXN-2026-00042",
  "amount_sar": 249.99,
  "channel": "ecom",
  "merchant_category": "electronics",
  "customer_id": "CUST-00077",
  "timestamp": "2026-07-05T03:30:00+00:00"
}
~~~

The response includes `transaction_id`, `fraud_probability`, `decision`, `model_version`, and `trace_id`.

| Endpoint | Simple explanation |
| :--- | :--- |
| `POST /v1/predict` | Score a transaction and return a decision. |
| `GET /v1/health` | Is the application process alive? |
| `GET /v1/ready` | Is the trained model loaded and ready? |
| `GET /docs` | Explore the API in Swagger UI. |

**Health ≠ readiness:** a running process may not yet be ready to make predictions.

## 05 · Testing & Automation

Testing here is about more than checking if the server returns HTTP 200.

| Test level | What it checks |
| :--- | :--- |
| **Unit** | Small rules and feature calculations. |
| **Integration** | The API contract, errors, and invalid payloads. |
| **Behavioural** | Important expectations about model decisions. |
| **Golden-file regression** | Scoring stays aligned with **5,000** trusted expected results. |

~~~bash
# Fast checks with coverage
python -m pytest -m "not slow" --cov --cov-report=term-missing --cov-fail-under=80

# The slow, full golden-file test
python -m pytest -m slow

# Code quality and architecture checks
python -m ruff check src tests
python -m mypy src/fraud_service
lint-imports
~~~

**Recorded GitHub Actions result, 24 Nov 2026:** **70 tests passed**, **1 slow test deselected**, and **98.46% coverage** in the per-commit test job. The slower golden-file regression is also included in the nightly workflow.

### From pull request to published image

~~~mermaid
flowchart TD
    PR["Pull request"] --> L["Lint + type checks<br/>+ architecture rules"]
    PR --> T["Tests + coverage gate"]
    L --> I["Docker image smoke test"]
    T --> I
    I --> R["Review and merge"]
    R --> M["Push to main"]
    M --> P["Publish container image to GHCR"]
    N["Nightly schedule"] --> S["Full suite, including slow tests"]
    classDef pink fill:#FCE7F3,stroke:#BE185D,color:#500724;
    class PR,L,T,I,R,M,P,N,S pink;
~~~

The workflows live in [`ci.yml`](.github/workflows/ci.yml) and [`nightly.yml`](.github/workflows/nightly.yml).

## 06 · The Numbers Behind the Improvements

These are **observed workshop results**, not promises for other computers or production environments.

| Experiment | Before | After | Observation |
| :--- | ---: | ---: | :--- |
| First request with warm-up | 41.225 ms | 21.798 ms | About **47%** lower first-request time. |
| Docker image size | 3.33 GB | 846 MB | Multi-stage build produced a smaller image. |
| p99 latency comparison | 139.5 ms (4 local workers) | 85.0 ms (Docker) | Docker run was faster *in this test*; controlled repeats would be needed to explain why. |
| CI image-smoke job | 144 s | 37 s | Later build benefited from caching; run conditions were not identical. |

Full evidence and caveats: [`BENCHMARKS.md`](BENCHMARKS.md).

## 07 · Security by Design

- **Fail fast:** If the model file is missing, startup stops with a useful error.
- **Typed settings:** Invalid thresholds and log levels are rejected.
- **Private by default:** The prediction log avoids raw customer feature values.
- **Masked secrets:** Sensitive log fields are replaced before JSON is rendered.
- **Traceable requests:** A trace ID makes it easier to investigate a problem.
- **Secret-leak drill:** Deleting a token from a file does **not** erase it from Git history.

For a real leak, the first action is to **revoke or rotate the credential**, then clean up history and improve scanning. Details: [`INCIDENT.md`](INCIDENT.md).

## 08 · Project Structure

~~~text
.
├── .github/workflows/      # CI and nightly checks
├── configs/                # Sample and development settings
├── data/                   # Sample transactions and golden scores
├── models/                 # Trained model bundle
├── payloads/               # Example and invalid API requests
├── scripts/                # Load tests and golden-result checks
├── src/fraud_service/
│   ├── domain/             # Transactions, features, decisions
│   ├── service/            # Scoring logic and model interface
│   ├── adapters/           # scikit-learn connection
│   ├── api/                # FastAPI app and schemas
│   ├── batch.py            # Batch scoring
│   ├── config.py           # Typed settings
│   └── logging_setup.py    # Structured JSON logs
├── tests/
│   ├── unit/
│   ├── integration/
│   └── behavioural/
├── BENCHMARKS.md
├── INCIDENT.md
├── Dockerfile
└── docker-compose.yml
~~~

## 09 · What This Project Taught Me

**A prediction is a result. Engineering makes that result usable, testable, traceable, and maintainable.**

Sometimes the biggest failures are small: a single comparison operator, an unvalidated setting, a risky log line, or an unchecked pull request.

I wanted this project to show not only **what I built**, but **why each part matters**.

---

<div align="center">

**Built by Jana Alhumaizi**  
*Computer Science · SDAIA Academy SDA-AIE-113 Workshop*

[Workshop](https://aie113.ibrahimalshehri.sa/) · [Original course repository](https://github.com/snow10100/fraud-service) · [Benchmarks](BENCHMARKS.md)

</div>
