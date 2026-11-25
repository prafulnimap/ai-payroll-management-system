from app.services.vector_store import vectorstore

print("--- 1. Payslip search, filtered to user 2 for may ---")
results = vectorstore.similarity_search_with_score(
    "What was my take home pay in May?",
    k=2,
    filter={"$and": [{"user_id": 2}, {"type": "payslip"}]},
)
for doc, score in results:
    print(round(score, 3), doc.page_content, doc.metadata)

print("\n--- 2. Same question, filtered to user 99 (should return nothing) ---")
print(
    vectorstore.similarity_search(
        "What was my take home pay in May?",
        k=2,
        filter={"$and": [{"user_id": 99}, {"type": "payslip"}]},
    )
)

print("\n--- 3. Policy search (global) ---")
for doc in vectorstore.similarity_search(
    "How is overtime paid?", k=2, filter={"type": "policy"}
):
    print(doc.page_content)
print("\n--- Payslips stored in Chroma for user 2 ---")

stored = vectorstore.get(
    where={"$and": [{"user_id": 2}, {"type": "payslip"}]},
    include=["documents", "metadatas"],
)

for document, metadata in zip(stored["documents"], stored["metadatas"]):
    print(document)
    print(metadata)
    print("-" * 50)
print("\n--- Policy indexing test ---")

results = vectorstore.similarity_search(
    "How many paid leaves can an employee take per year?",
    k=3,
    filter={"type": "policy"},
)

for doc in results:
    print(doc.page_content)
    print(doc.metadata)
    print("-" * 50)
