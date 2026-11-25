from app.ai.graph import ask

tests = [
    (2, "What was my highest deduction this year?"),
    (2, "What was my total salary in 2026?"),
    (2, "What was my lowest net salary ever?"),
    (2, "Tell me my salary of January and February 2025"),
    (2, "Why was my salary different last month?"),
    (2, "Compare my last two payslips"),
]

for user_id, question in tests:
    result = ask(question, user_id)
    print(f"[user {user_id}] Q: {question}")
    print(f"  A: {result['answer']}")
    print(f"  Sources: {result['sources']}\n")
