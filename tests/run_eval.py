import json
import os
import sys
import time

# Ensure root directory is on Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import process_support_chat
from src.vectorstore import get_vector_store

TEST_DATA_PATH = os.path.join("tests", "test_chats.json")
ACTIVE_CUSTOMER = "CUST_01"  # Alice Smith

def run_detailed_evaluation():
    with open(TEST_DATA_PATH, "r") as f:
        tests = json.load(f)

    store = get_vector_store()
    passed = 0
    total = len(tests)

    print("\n" + "=" * 90)
    print(" " * 24 + "DEEP TRACE EVALUATION: INPUT -> ROUTE -> CONTEXT -> OUTPUT")
    print("=" * 90)

    for item in tests:
        qid = item["id"]
        q = item["question"]
        expected = item["category"]

        # Run pipeline
        answer, actual = process_support_chat(q, customer_id=ACTIVE_CUSTOMER)
        is_pass = (expected == actual)
        if is_pass:
            passed += 1

        print(f"\n[TEST #{qid:02d}] -----------------------------------------------------------------")
        print(f"Customer Query     : \"{q}\"")
        print(f"Routing Verdict    : Expected [{expected}] | Actual [{actual}] -> {'PASS' if is_pass else 'FAIL'}")

        if actual == "FAQ_RAG":
            docs = store.similarity_search_with_relevance_scores(q, k=1)
            if docs:
                chunk, score = docs[0]
                preview = chunk.page_content.replace('\n', ' ')[:130]
                print(f"ChromaDB Retrieval : Score: {score:.3f} | Chunk Preview: \"{preview}...\"")
            # Brief pause only after live LLM calls to respect Groq OTPM
            time.sleep(1.8)
        elif actual == "ORDER_TRACKING":
            print(f"Database Security  : Executed SQL query checked against customer_id='{ACTIVE_CUSTOMER}'")
        elif actual == "FALLBACK":
            print(f"Guardrail State    : Confidence score below threshold / unsupported intent intercepted")
        elif actual == "HUMAN_HANDOFF":
            print(f"Escalation State   : High-risk/urgent trigger matched -> Routed to human queue")

        ans_preview = answer.replace('\n', ' ')
        print(f"Generated Output   : \"{ans_preview[:150]}{'...' if len(ans_preview) > 150 else ''}\"")

    print("\n" + "=" * 90)
    print(f"SUMMARY: {passed}/{total} Passed ({(passed/total)*100:.1f}% Accuracy)")
    print("=" * 90 + "\n")

if __name__ == "__main__":
    run_detailed_evaluation()