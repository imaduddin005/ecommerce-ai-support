ecommerce AI Support Assistant
A hybrid AI-powered customer support automation prototype designed to handle repetitive e-commerce inquiries under a $0 budget constraint.
Built using Python, LangChain (LCEL), Groq, ChromaDB, Sentence Transformers, and SQLite, the system combines rule-based routing, semantic intent classification, RAG, and secure database lookups.
 Key Features
- Hybrid Routing: Combines rule-based heuristics and LLM-based semantic classification.
- FAQ Support (RAG): Retrieves answers from store policies using ChromaDB.
- Order Tracking: Retrieves order information through SQLite.
- IDOR Protection: Enforces customer-level access restrictions using parameterized SQL queries.
- Human Handoff: Escalates damaged product complaints and payment disputes.
- Guardrails: Handles unsupported questions without inventing information.
- Typo Tolerance: Handles informal language, spelling mistakes, and incorrect grammar.


 System Architecture
       [ Customer Query ]
               |
       [ Hybrid Router ]
               |
       +-------+--------+
       |       |        |
       v       v        v
     FAQ    ORDER    HUMAN
     RAG   TRACKING  HANDOFF
       |       |        |
       v       v        v
   ChromaDB  SQLite  Support Agent
       |
       v
  [ Fallback / Guardrails ]


Routing Strategy:
1. Tier 1 – Fast Path: Regex and keyword matching for high-confidence queries.
2. Tier 2 – Semantic Classification: Groq LLM with Pydantic structured output for ambiguous queries.
3. Specialized Handlers: FAQ RAG, secure order tracking, or human escalation.
 Technology Stack
TechnologyPurposePythonCore developmentLangChain (LCEL)AI orchestrationGroq (Qwen)LLM inferenceChromaDBVector storageSentence TransformersLocal embeddingsall-MiniLM-L6-v2Embedding modelSQLiteOrder databasePydanticStructured output validation
 Evaluation Results
Tested against 40 benchmark customer support queries.
CategoryTest CasesPassedFAQ & Policy RAG2020Order Tracking88Guardrails & Fallback66Human Escalation66Total4040
<badge color="success">40/40 Tests Passed</badge>



📁 Project Structure
ecommerce-ai-support/
├── data/
│   ├── help_docs.md
│   └── orders.db
├── src/
│   ├── agent.py
│   ├── chains.py
│   ├── database.py
│   └── vectorstore.py
├── tests/
│   ├── run_eval.py
│   └── test_queries.json
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md




 Installation & Execution
1. Clone the repository
git clone https://github.com/imaduddin005/ecommerce-ai-support.git
cd ecommerce-ai-support


2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
4. Configure environment variables
Create a .env file:
GROQ_API_KEY=your_groq_api_key
5. Initialize the vector store
python -m src.vectorstore
6. Run evaluation tests
python tests/run_eval.py
7. Start the application
python app.py



 Sample Interaction
Customer: What is your return policy?
Assistant [FAQ_RAG]: You can request a return or exchange within 30 days of parcel delivery, provided items are unused and in original packaging.
Customer: Where is order ORD1004?
Assistant [ORDER_TRACKING]: Access Denied: You are not authorized to view details for this order.
Customer: My parcel arrived damaged.
Assistant [HUMAN_HANDOFF]: I apologize for the inconvenience. Your issue has been escalated to human support.




 Current Limitations
- Stateless conversations without persistent memory.
- Read-only order database.
- Limited Roman Urdu language support.
- CLI-based prototype without website integration.


 Future Improvements
- Add Redis-based conversation memory.
- Integrate FastAPI and an e-commerce website.
- Support secure order cancellation.
- Improve multilingual and Roman Urdu understanding.
- Add monitoring and performance evaluation.
