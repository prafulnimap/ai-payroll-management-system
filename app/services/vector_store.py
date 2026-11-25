import calendar
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models import Payslip, Policy

# 1. The embedding model (runs locally, free)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 2. The vector database (saved to the ./chroma_db folder, so data survives restarts)
vectorstore = Chroma(
    collection_name="payroll",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
)

# 3. Splits long policies into smaller chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def _money(value) -> str:
    return f"₹{value:,.2f}"


# ---------------- PAYSLIPS ----------------


def payslip_to_text(p: Payslip, employee_name: str) -> str:
    """Manual summary of structured data, written as natural sentences."""
    month_name = calendar.month_name[p.month]
    return (
        f"Payslip for {employee_name} (employee ID {p.user_id}) for {month_name} {p.year}. "
        f"Gross salary: {_money(p.gross_salary)}. "
        f"Bonuses: {_money(p.bonuses)}. "
        f"Total deductions: {_money(p.deductions)}. "
        f"Net salary (take-home pay): {_money(p.net_salary)}."
    )


def index_payslip(p: Payslip, employee_name: str) -> None:
    doc_id = f"payslip-{p.id}"
    doc = Document(
        page_content=payslip_to_text(p, employee_name),
        metadata={
            "type": "payslip",
            "user_id": p.user_id,
            "month": p.month,
            "month_name": calendar.month_name[p.month],
            "year": p.year,
        },
    )
    vectorstore.delete(ids=[doc_id])  # remove the old version (if any)
    vectorstore.add_documents([doc], ids=[doc_id])


def delete_payslip_vectors(payslip_id: int) -> None:
    vectorstore.delete(ids=[f"payslip-{payslip_id}"])


# ---------------- POLICIES ----------------


def delete_policy_vectors(policy_id: int) -> None:
    found = vectorstore.get(where={"policy_id": policy_id})
    if found["ids"]:
        vectorstore.delete(ids=found["ids"])


def index_policy(policy: Policy) -> None:
    delete_policy_vectors(policy.id)  # chunk count may change on edit
    chunks = splitter.split_text(policy.content)
    docs, ids = [], []
    for i, chunk in enumerate(chunks):
        docs.append(
            Document(
                page_content=f"{policy.title}: {chunk}",  # title in every chunk helps retrieval
                metadata={
                    "type": "policy",
                    "policy_id": policy.id,
                    "title": policy.title,
                },
            )
        )
        ids.append(f"policy-{policy.id}-{i}")
    vectorstore.add_documents(docs, ids=ids)
