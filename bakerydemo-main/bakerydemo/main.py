from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import boto3
import os
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings

from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter

app = FastAPI()

# Input schema
class QueryRequest(BaseModel):
    query: str
    index_id: str
    top_k: int = 5

# AWS Kendra query
def query_kendra(query, index_id, top_k):
    region = os.getenv("AWS_REGION", "us-east-1")

    # Initialize Kendra client with region
    kendra = boto3.client('kendra', region_name=region)
    response = kendra.query(QueryText=query, IndexId=index_id)
    docs = []
    for item in response.get("ResultItems", [])[:top_k]:
        excerpt = item.get("DocumentExcerpt", {}).get("Text", "")
        if excerpt:
            docs.append(excerpt)
    return docs

# RAG pipeline
def rag_query(query: str, index_id: str, top_k: int = 5):
    docs = query_kendra(query, index_id, top_k)
    documents = [Document(page_content=d) for d in docs]

    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(documents)

    vectorstore = FAISS.from_documents(split_docs, OllamaEmbeddings(model="tinyllama:latest"))
    llm = Ollama(model="tinyllama:latest")

    chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())
    return chain.run(query)

# API endpoint
@app.post("/rag/")
async def rag_handler(payload: QueryRequest):
    result = rag_query(payload.query, payload.index_id, payload.top_k)
    return {"query": payload.query, "result": result}
