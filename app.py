import sys
from src.agent import process_support_chat

BANNER = """
===========================================================
🛍️  E-Commerce Support Assistant (CLI Mode)
===========================================================
- Session Authenticated as: CUST_01 (imad)
- Type your questions below.
- Type 'exit', 'quit', or 'q' to leave the chat.
===========================================================
"""

def run_cli():
    print(BANNER)
    customer_id = "CUST_01"

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nThank you for reaching out. Have a great day!")
                sys.exit(0)

            # Route through the unified LangChain agent
            response, route = process_support_chat(user_input, customer_id=customer_id)

            print(f"\nAssistant [{route}]:\n{response}")

        except KeyboardInterrupt:
            print("\nExiting chat session.")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: An unexpected error occurred: {e}")

if __name__ == "__main__":
    run_cli()