import os
import pandas as pd
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.storage.file_system import LocalFileStore

# Initialize local disk cache directory
cache_dir = os.path.join(os.path.dirname(__file__), ".cache", "embeddings")
os.makedirs(cache_dir, exist_ok=True)
store = LocalFileStore(cache_dir)

df = pd.read_csv("company_faq.csv")
base_embeddings = OllamaEmbeddings(
    model="nomic-embed-text:latest",
    keep_alive= 300,
    base_url="http://localhost:11434"  # Windows/Mac: connects to host
)

# Safe namespace replacement for Windows (no colons in filename paths)
safe_namespace = base_embeddings.model.replace(":", "_")

# Wrap embeddings to cache both documents and queries
cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings=base_embeddings,
    document_embedding_cache=store,
    namespace=safe_namespace,
    query_embedding_cache=True
)

db_location = "chrome_langchain_db"
add_documents = not os.path.exists(db_location)

vector_store = Chroma(
    collection_name="company_faq", 
    embedding_function=cached_embeddings, 
    persist_directory=db_location
)

if add_documents:
    documents = []

    for idx, row in df.iterrows():
        document = Document(
            page_content=f""" Question: {row['question']} Answer: {row['answer']} """,
            metadata={"source": "company_faq.csv", "id": row["id"], "category": row["category"]},
        )
        documents.append(document)

    vector_store.add_documents(documents=documents)

# Format documents for readability in LLM context
# def format_docs(docs):
#     """Format retrieved documents as readable text for the LLM"""
#     formatted = []
#     for doc in docs:
#         formatted.append(f"Q: {doc.page_content}")
#     return "\n\n".join(formatted)


# #Context builder with relevance scores
# #Add more results from other sources here itself
# def build_context(query):
#     results = vector_store.similarity_search_with_relevance_scores(
#         query,
#         k=3
#     )
#     context_parts = []
#     best_score = results

#     for doc, score in results:
#         context_parts.append(doc.page_content)

#     context = "\n\n".join(
#         doc.page_content
#         for doc, _ in results
#     )

#     return context, best_score, results
    
# base_retriever = vector_store.as_retriever(search_kwargs={"k": 3})
# retriever = base_retriever | RunnableLambda(format_docs)

def retrieve_with_confidence(query):
    results = vector_store.similarity_search_with_relevance_scores(
        query,
        k=3
    )

    if not results:
        return "", 0.0, []

    context = "\n\n".join(
        doc.page_content for doc, _ in results
    )

    best_score = results[0][1]

    return context, best_score, results


