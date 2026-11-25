# AI Sentinel — Enterprise AI Agent Validation Suite

AI Sentinel is an independent, enterprise-inspired AI Agent Validation Suite. It stress-tests and validates conversational AI agents before they are deployed to production. By simulating adversarial customer interactions, scoring conversation quality through an AI Evaluation Engine, and recommending automatic prompt repairs, AI Sentinel helps product managers and QA teams catch compliance, safety, and hallucination issues early.

---

## 🛑 The Problem

When enterprises deploy AI chat or voice agents, they often behave unpredictably under difficult real-world conditions. Edge cases—such as hostile customers, bilingual inputs, abrupt topic switching, policy exception pressures, and direct prompt injection (jailbreak) attempts—are rarely anticipated during initial development. 

Discovering these failures after deployment is expensive, leads to poor customer experiences, and can expose the company to safety, brand, or financial risks (e.g., promising unauthorized refunds or leaking internal instructions).

---

## 🛡️ The Solution

AI Sentinel automates the entire pre-deployment QA lifecycle for conversational agents:
1. **Dynamic Persona Generation**: Leverages Gemini 3.8 Flash (`gemini-3.8-flash`) to build custom, context-relevant customer personas designed to exploit policy boundaries.
2. **Adversarial Dialogue Simulation**: Runs multi-turn conversation loops between the candidate agent and the persona in parallel.
3. **AI Evaluation Engine**: Evaluates completed chats on core metrics (Instruction Following, Safety, Hallucination, Policy Compliance, and Conversation Recovery).
4. **Prompt Optimization**: Automatically analyzes failures to generate an upgraded prompt (v2.0) with defensive constraints and projects expected reliability scores.
5. **Executive Dossier**: Compiles all findings into a stakeholder-ready, downloadable PDF validation report.

---

## 📐 Architecture & Pipeline Data Flow

AI Sentinel uses a closed-loop validation architecture to evaluate, diagnose, and repair system prompts.

```
                  +------------------------------------------+
                  |               User Inputs                |
                  |     (System Prompt + Knowledge Base)     |
                  +---------------------+--------------------+
                                        |
                                        v
                  +---------------------+--------------------+
                  |         1. Dynamic Persona Generator     |
                  |     (Gemini 3.8 Flash profiles)        |
                  +---------------------+--------------------+
                                        |
                                        v
                  +---------------------+--------------------+
                  |       2. Parallel Conversation Simulator  |
                  |        (3-5 turn adversarial chats)      |
                  +---------------------+--------------------+
                                        |
                                        v
                  +---------------------+--------------------+
                  |         3. AI Evaluation Engine          |
                  |        (LLM Judge scoring transcripts)   |
                  +---------------------+--------------------+
                                        |
                                        v
                  +---------------------+--------------------+
                  |             4. Metrics Engine            |
                  |       (Reliability scoring & KPIs)       |
                  +---------------------+--------------------+
                                        |
                                        v
                  +---------------------+--------------------+
                  |       5. Dashboard / PDF Report / v2     |
                  |     (Stakeholder dossier & Prompt v2)    |
                  +---------------------+--------------------+
```

---

## ✨ Key Features & Pages

* **🎯 Home & Configuration**: Configure validation sessions. Paste your agent's system prompt and optional FAQ context. Check the adversarial scenarios to run. Includes a **"Load Sample Agent Template"** button to load a retail return assistant for instant, zero-setup testing.
* **📊 Evaluation Dashboard**: High-level visual KPI cards (Overall Reliability, Prompt Robustness, Critical Failures, and Deployment Risk), best/worst performing personas, and Plotly charts showing score distributions and failure categories.
* **🔍 Failure Explorer**: Drill down into specific dialogue logs. Displays transcripts in styled chat bubbles side-by-side with the AI Evaluation Engine's rating scores, failure category, failure reason, and recommended prompt repair.
* **⚡ Prompt Optimizer**: Compares original instructions side-by-side with an LLM-engineered v2.0 prompt, highlighting improvements (e.g. security leakage guards, strict refund limits) and a projected score.
* **📐 Architecture Diagram**: An interactive system map explaining the data pipeline, showcasing robust AI product engineering and design thinking.

---

## 🛠️ Tech Stack

* **Frontend & Dashboard**: Python Streamlit (custom CSS injected for a premium enterprise light-themed layout).
* **AI Orchestration**: Gemini API via `google-genai` Python SDK.
* **Concurrency**: `ThreadPoolExecutor` for parallel scenario simulations.
* **Data Processing**: Pandas.
* **Visualizations**: Plotly (horizontal bar charts, pie charts, score cards).
* **Report Generation**: ReportLab PDF library (styled with cover pages, grids, and appendix traces).

---

## 🚀 Running Locally

### 1. Prerequisites
Make sure you have Python installed:
```bash
python --version  # Recommended Python 3.10+
```

### 2. Clone and Install Dependencies
Navigate to the directory and run:
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
Run the Streamlit server:
```bash
streamlit run app.py
```

### 4. Provide API Key (Optional)
* To run **Live Evaluations** using Gemini, input your API key in the sidebar text field, copy `.env.example` to `.env`, or set the environment variable:
  ```bash
  export GEMINI_API_KEY="your-api-key-here"
  ```
* Optionally override the Gemini model via `GEMINI_MODEL` (defaults to `gemini-3.8-flash`).
* If no key is provided, the application runs in **Offline Sample Demo Mode**, leveraging pre-compiled validation results from a sample e-commerce agent to enable immediate exploration.

---

## ☁️ Deployment

### Streamlit Community Cloud
1. Push this repository to GitHub.
2. Create a new app in Streamlit Community Cloud pointing to `app.py`.
3. Under **Advanced settings → Secrets**, optionally add:
   ```toml
   GEMINI_API_KEY = "your-api-key-here"
   ```

### Docker (Cloud Run / Render / Railway / Self-Hosted)
```bash
docker build -t ai-sentinel .
docker run -p 8501:8501 -e GEMINI_API_KEY="your-api-key-here" ai-sentinel
```
The container exposes port `8501` (or respects `$PORT`) and includes a `/_stcore/health` healthcheck.

### Running Tests
```bash
python -m unittest discover -s tests -v
```

---

## 📸 Demo Screenshots
* **Home & Configuration Panel**: Setup target agent prompt, knowledge base constraints, and select scenario types.

![alt text](image-1.png)

* **Evaluation Dashboard**: Visual summary of Overall Reliability, Prompt Robustness, Deployment Risk rating, and Plotly analytics.
![alt text](image-2.png)
* **Failure Explorer**: Step-by-step chat history alongside safety compliance logs and recommended prompt repairs.
![alt text](image-3.png)
* **Prompt Optimizer**: Side-by-side prompt v1.0 vs v2.0 comparisons and PDF downloads.
![alt text](image-4.png)

---

## 🔮 Future Improvements

* **Voice Stress-Testing**: Simulate voice responses to measure latency, background noise resistance, word slurring, speech interruptions, and emotional tone matching.
* **CI/CD Quality Gates**: Integrate AI Sentinel as a GitHub Action or build step that runs automatically whenever prompts change, blocking deployments if reliability drops below a 90% threshold.
* **Human-in-the-Loop Override**: Allow QA leads to manually review and flag LLM-evaluator assessments, creating a fine-tuning dataset to customize evaluation rules over time.
