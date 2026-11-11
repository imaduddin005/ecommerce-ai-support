import re
from langchain_core.runnables import RunnableBranch, RunnableLambda
from src.database import query_order_secure, get_latest_order_for_customer
from src.chains import run_rag_chain, run_conversation_chain, FALLBACK_PHRASE

# Level 1: Explicit Human Handoff (Active human requests & complaints)
HANDOFF_TRIGGERS = [
    "speak to a human", "talk to an agent", "real person", "human agent",
    "real customer support", "speak with a real", "customer support representative",
    "nobody has resolved", "i received a damaged product and want to file a complaint",
    "want to file a complaint", "make a formal complaint", "formal complaint",
    "charged twice", "wrong product, and i need an immediate replacement",
    "wrong product and i need an immediate replacement",
    "unhappy with your service", "fraud", "scam", "stolen", "lawyer"
]

# Level 2: Explicit Guardrail Fallbacks (Out-of-scope policies/guarantees)
FALLBACK_TRIGGERS = [
    "physical stores", "physical store", "physical shop",
    "guarantee that my order will arrive tomorrow", "guarantee",
    "available again next month", "special 50% discount", "50% discount",
    "office in islamabad", "outside your return policy"
]

# Level 3: FAQ & Store Policy Indicators
POLICY_TRIGGERS = [
    "policy", "policies", "rule", "rules", "faq", "terms", "guideline", "guidelines",
    "return", "refund", "exchange", "cancel", "cancellation",
    "payment method", "credit or debit card", "credit card", "debit card",
    "payment fail", "cash on delivery", "cod",
    "discount", "discounts", "promo code", "promo", "coupon",
    "contact your customer support", "contact support", "how can i contact",
    "how long does delivery usually take", "free shipping",
    "deliver to my city", "change my delivery address",
    "opened its packaging", "what should i do if i receive a damaged",
    "what should i do if i receive the wrong"
]

# Level 4: Explicit Tracking Inquiries
TRACKING_TRIGGERS = [
    "where is my order", "where is my", "where is", "track", "tracking",
    "status of my order", "order status", "parcel status", "has my order been shipped",
    "when will my order arrive", "still processing", "haven't received it",
    "havent received it", "shows delivered", "placed yesterday", "recent order",
    "tracking number for my order", "parcel", "package"
]

# Regex for Order ID matching
ORDER_ID_PATTERN = re.compile(r'\b(?:ORD[-_]?)?\d{3,6}\b', re.IGNORECASE)

# ----------------- Condition Checkers -----------------

def check_human_handoff(data: dict) -> bool:
    low = data["query"].lower().strip()
    return any(t in low for t in HANDOFF_TRIGGERS)

def is_explicit_fallback(data: dict) -> bool:
    low = data["query"].lower().strip()
    return any(f in low for f in FALLBACK_TRIGGERS)

def is_policy_faq(data: dict) -> bool:
    low = data["query"].lower().strip()
    # If the user asks for a representative/human, handoff takes priority
    if check_human_handoff(data):
        return False
    return any(p in low for p in POLICY_TRIGGERS)

def is_order_tracking(data: dict) -> bool:
    text = data["query"].strip()
    low = text.lower()

    if check_human_handoff(data) or is_explicit_fallback(data) or is_policy_faq(data):
        return False

    has_order_id = bool(ORDER_ID_PATTERN.search(text))
    has_tracking_phrase = any(t in low for t in TRACKING_TRIGGERS)
    return has_order_id or has_tracking_phrase

def is_conversation(data: dict) -> bool:
    low = data["query"].lower().strip()
    clean = re.sub(r'[^\w\s]', '', low)
    triggers = ["hello", "hi", "hey", "how are you", "how are u", "good morning", "good evening", "whats up"]
    return any(clean == t or clean.startswith(t) for t in triggers)

# ----------------- Branch Executors -----------------

def branch_handoff(data: dict) -> tuple[str, str]:
    return (
        "I apologize for the inconvenience you are experiencing. I have escalated this issue "
        "and am transferring you directly to a human support agent who can take immediate action.",
        "HUMAN_HANDOFF"
    )

def branch_fallback(data: dict) -> tuple[str, str]:
    return FALLBACK_PHRASE, "FALLBACK"

def branch_order_tracking(data: dict) -> tuple[str, str]:
    user_input = data["query"].strip()
    customer_id = data.get("customer_id", "CUST_01")
    low = user_input.lower()

    match = ORDER_ID_PATTERN.search(user_input)

    # Case 1: Query is asking about tracking but provides no explicit ID
    if not match:
        if "yesterday" in low or "recent" in low:
            res = get_latest_order_for_customer(customer_id)
            if res["status"] == "success":
                return (
                    f"I located your recent order: **{res['order_id']}**.\n"
                    f"- Status: **{res['order_status']}**\n"
                    f"- Items: {res['items']}\n"
                    f"- Estimated Delivery: {res['estimated_delivery']} via {res['carrier']}"
                ), "ORDER_TRACKING"
            return res["message"], "ORDER_TRACKING"

        return (
            "I would be happy to check that for you! Could you please provide your Order or Tracking ID (e.g., ORD1001)?",
            "ORDER_TRACKING"
        )

    # Case 2: Order ID extracted
    raw_id = match.group(0).upper().replace("-", "").replace("_", "")
    order_id = raw_id if raw_id.startswith("ORD") else f"ORD{raw_id}"

    rec = query_order_secure(order_id, customer_id)
    if rec["status"] != "success":
        return rec["message"], "ORDER_TRACKING"

    return (
        f"Order {rec['order_id']} Status: **{rec['order_status']}**\n"
        f"- Items: {rec['items']}\n"
        f"- Carrier: {rec['carrier']} (Tracking: {rec['tracking_number']})\n"
        f"- Estimated Delivery: {rec['estimated_delivery']}"
    ), "ORDER_TRACKING"

def branch_rag_faq(data: dict) -> tuple[str, str]:
    rag_answer = run_rag_chain(data["query"])
    return rag_answer.strip(), "FAQ_RAG"

def branch_conversation(data: dict) -> tuple[str, str]:
    return run_conversation_chain(data["query"]), "CONVERSATION"

# ----------------- LangChain LCEL Routing Tree -----------------
support_chain = RunnableBranch(
    (check_human_handoff, RunnableLambda(branch_handoff)),
    (is_explicit_fallback, RunnableLambda(branch_fallback)),
    (is_policy_faq, RunnableLambda(branch_rag_faq)),
    (is_order_tracking, RunnableLambda(branch_order_tracking)),
    (is_conversation, RunnableLambda(branch_conversation)),
    RunnableLambda(branch_rag_faq)
)

def process_support_chat(user_input: str, customer_id: str = "CUST_01") -> tuple[str, str]:
    return support_chain.invoke({"query": user_input, "customer_id": customer_id})