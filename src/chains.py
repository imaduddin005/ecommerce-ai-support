import os
import re
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.vectorstore import get_vectorstore

load_dotenv()

FALLBACK_PHRASE = (
    "I'm sorry, but I don't have enough information to answer this question accurately. "
    "I don't want to provide incorrect information. Would you like me to connect you with our support team?"
)

EXPLICIT_OUT_OF_SCOPE = [
    "physical store", "physical shop", "physical stores", "outlet", "walk-in",
    "guarantee that my order will arrive tomorrow", "guarantee",
    "available again next month",
    "special 50% discount", "50% discount",
    "office in islamabad",
    "outside your return policy"
]

# ----------------- Structured Intent Models & Classifier -----------------

class SemanticIntent(BaseModel):
    intent: Literal["ORDER_TRACKING", "POLICY_FAQ", "HUMAN_HANDOFF", "CONVERSATION", "FALLBACK"] = Field(
        description="The true underlying operational intent of the customer inquiry."
    )
    extracted_order_id: str | None = Field(
        default=None,
        description="Extracted Order ID if explicitly stated (e.g., ORD1001, 1001), otherwise null."
    )

CLASSIFICATION_SYSTEM_PROMPT = """You are an expert semantic intent classifier for an e-commerce support system.
Analyze the customer message and classify its TRUE semantic intent, ignoring typos, broken English, and grammatical errors:

- ORDER_TRACKING:
  Inquiries about shipment status, delivery date, package arrival, dispatch, or order location.
  Examples: "have my order has dispachecd oor shipeed yes or know", "where is my parcel", "packet not reach yet", "ord1001 status", "when will it arrive".

- HUMAN_HANDOFF:
  Reporting broken/damaged/defective items, duplicate charges, serious complaints, or demanding a human representative.
  Examples: "parcel damage arrived", "broken shirt refund", "charged two times from my card", "talk to human", "formal complaint".

- POLICY_FAQ:
  Questions about general store policies, return/exchange duration, refund timelines, payment methods (COD, cards), delivery charges, discounts.
  Examples: "what is your return policy", "how long does refund take", "do you accept cash on delivery", "how to apply coupon".

- CONVERSATION:
  Greetings, pleasantries, small talk.
  Examples: "hello", "hi", "how are you", "good morning".

- FALLBACK:
  Out-of-scope inquiries or unsupported commitments.
  Examples: "do you have physical shop in islamabad", "give me special 50% discount", "guarantee arrival tomorrow".

Customer message: {query}
"""

# ----------------- Prompts -----------------

RAG_SYSTEM_PROMPT = """You are the official customer support AI for an e-commerce platform.
Answer the customer's question directly, clearly, and concisely using ONLY the provided Store Documentation.

Strict Rules:
1. Base your answer strictly on the Context below. Do NOT extrapolate or assume details.
2. If the answer cannot be found in the Context, respond EXACTLY with:
   "{fallback_phrase}"
3. Do not state "according to the document" or "based on the context". Answer naturally and professionally.
4. Keep the answer brief and factual (2-4 sentences).

Context:
{context}

Customer Question:
{question}
"""

CONVERSATION_SYSTEM_PROMPT = """You are a helpful, polite, and authentic customer support AI for an e-commerce store.
Respond naturally, warmly, and concisely to the customer's greeting, small talk, or general remark.
If relevant, let them know you can help with parcel tracking or store policies."""

# ----------------- Core Functions -----------------

def get_llm(temperature: float = 0.0):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in environment or .env file.")
    return ChatGroq(
        model_name="qwen/qwen3.8-27b",
        temperature=temperature,
        max_tokens=300,
        api_key=api_key
    )

def classify_ambiguous_intent(query: str) -> SemanticIntent:
    """Used by Tier-2 router when fast-path heuristics encounter ambiguous/broken English."""
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(SemanticIntent)
    prompt = ChatPromptTemplate.from_template(CLASSIFICATION_SYSTEM_PROMPT)
    chain = prompt | structured_llm

    try:
        return chain.invoke({"query": query})
    except Exception:
        # Resilient fallback if API call fails
        low = query.lower()
        if any(w in low for w in ["order", "parcel", "ship", "track"]):
            return SemanticIntent(intent="ORDER_TRACKING")
        if any(w in low for w in ["damage", "broken", "complaint", "human"]):
            return SemanticIntent(intent="HUMAN_HANDOFF")
        return SemanticIntent(intent="POLICY_FAQ")

def run_rag_chain(query: str) -> str:
    low = query.lower().strip()

    if any(phrase in low for phrase in EXPLICIT_OUT_OF_SCOPE):
        return FALLBACK_PHRASE

    vs = get_vectorstore()
    docs = vs.similarity_search(query, k=2)

    if not docs:
        return FALLBACK_PHRASE

    context_text = "\n\n".join([d.page_content for d in docs])
    prompt = ChatPromptTemplate.from_template(RAG_SYSTEM_PROMPT)
    llm = get_llm(temperature=0.0)
    chain = prompt | llm | StrOutputParser()

    try:
        response = chain.invoke({
            "context": context_text,
            "question": query,
            "fallback_phrase": FALLBACK_PHRASE
        })
        return response.strip()
    except Exception as e:
        return f"Error connecting to support service: {e}"

def run_conversation_chain(query: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", CONVERSATION_SYSTEM_PROMPT),
        ("human", "{question}")
    ])
    llm = get_llm(temperature=0.4)
    chain = prompt | llm | StrOutputParser()
    try:
        return chain.invoke({"question": query}).strip()
    except Exception:
        return "Hello! I am doing well, thank you. How can I assist you with your orders or store policies today?"