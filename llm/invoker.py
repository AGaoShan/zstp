from pydantic import BaseModel, Field
from promptic import llm
from litellm import litellm
from llm.model import SecurityViewDimensions,AuditReport
litellm.api_key = "sk-Umy6QJiK8EY6Aco8EbriaMB1cw2nq15bY6y8OBM8mJUQTxcr"
litellm.api_base = "https://yunwu.ai/v1"
from dotenv import load_dotenv

load_dotenv()


@llm(
    # Use a model that supports structured output (e.g., gpt-4o or gpt-3.5-turbo)
    model="gpt-4o-mini",
    temperature=0.0  # Low temperature for structured tasks is recommended
)
def get_security_view_dimensions(code:str)->SecurityViewDimensions :
    """---ROLE---
You are a query transformation agent for a Graph-RAG based smart contract security audit system.

---TASK---
Your task is NOT to audit or confirm vulnerabilities.
Your task is to generate multiple independent “vulnerability hypotheses” from different security perspectives,
which will later be used as separate semantic queries for vector retrieval.

Do NOT merge perspectives.
Do NOT conclude that a vulnerability exists.
Only express plausible risk-oriented hypotheses.

---INPUT---
You will receive a piece of Solidity smart contract code.
{code}
---OUTPUT OBJECTIVE---
Generate multiple concise vulnerability hypotheses, each from a distinct security perspective.
Each hypothesis must be:
- Self-contained
- Suitable for embedding as an independent vector
- Focused on behavioral or structural risk patterns

---SECURITY PERSPECTIVES---
For each of the following perspectives, generate exactly ONE hypothesis:

1. Asset Safety Perspective
   Focus on risks related to:
   - Reentrancy
   - Flash loan abuse
   - Fund theft, lock, or unauthorized transfer
   - External calls affecting balance or state

2. Access Control Perspective
   Focus on risks related to:
   - Missing or incorrect access modifiers
   - Role misconfiguration
   - Privilege escalation
   - Improper authorization logic

3. Data & State Logic Perspective
   Focus on risks related to:
   - Integer overflow / underflow
   - Incorrect state updates
   - Inconsistent invariants
   - Dangerous assumptions in calculations or mappings

---OUTPUT FORMAT---
Output in the following strict structure:

[Asset Safety Hypothesis]
<one concise hypothesis sentence>

[Access Control Hypothesis]
<one concise hypothesis sentence>

[Data & State Logic Hypothesis]
<one concise hypothesis sentence>

---CONSTRAINTS---
- Do NOT reference line numbers
- Do NOT reference known vulnerability names directly unless logically implied
- Do NOT copy code snippets
- Do NOT speculate beyond what the code structure could reasonably suggest
- Do NOT rank or compare hypotheses
"""
    pass

@llm(
    # Use a model that supports structured output (e.g., gpt-4o or gpt-3.5-turbo)
    model="gpt-4o-mini",
    temperature=0.0  # Low temperature for structured tasks is recommended
)
def get_report(code: str,Top_Reranked_Findings)->AuditReport:
    """
        You are a highly experienced and meticulous Senior Solidity Smart Contract Security Auditor with 10 years of professional experience. Your task is to generate a professional, accurate, and actionable Final Security Audit Report based on the User Code Snippet and the relevant audit findings retrieved from the specialized knowledge graph.
    **Instructions:**
    1.  **STRICTLY use** the highest-ranked entry (index 0) in `Top_Reranked_Findings` as your core knowledge source.
    2.  **Analyze the User Code Snippet** to determine precisely how it matches the vulnerability pattern described by the top-ranked knowledge graph finding.
    3.  **Detail the vulnerability type, root cause, risk level, and professional remediation advice** based on the information provided by the knowledge graph.
    4.  **ALWAYS** use the structure defined in the **Output Format Requirements** section below to present your report.

    ### [INPUT DATA]

    #### 1. User Code Snippet (UserCodeSnippet)
    ```solidity
    {code}
    #### 2. Top_Reranked_Findings
    {Top_Reranked_Findings}
    """
    pass