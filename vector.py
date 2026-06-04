import os
import pandas as pd
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

df = pd.read_csv("company_faq.csv")
embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")

db_location = "chrome_langchain_db"
add_documents = not os.path.exists(db_location)

vector_store = Chroma(
    collection_name="company_faq", 
    embedding_function=embeddings, 
    persist_directory=db_location
)

if add_documents:
    documents = []

    for idx, row in df.iterrows():
        document = Document(
            page_content=row["question"] + " " + row["answer"],
            metadata={"source": "company_faq.csv", "id": row["id"], "category": row["category"]},
        )
        documents.append(document)

    vector_store.add_documents(documents=documents)

# Format documents for readability in LLM context
def format_docs(docs):
    """Format retrieved documents as readable text for the LLM"""
    formatted = []
    for doc in docs:
        formatted.append(f"Q: {doc.page_content}")
    return "\n\n".join(formatted)

base_retriever = vector_store.as_retriever(search_kwargs={"k": 3})
retriever = base_retriever | RunnableLambda(format_docs)
