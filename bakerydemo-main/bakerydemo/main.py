from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import boto3
import os
import logging
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings

from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter

# Import our custom Bedrock embeddings
from bakerydemo.chatbot.bedrock_embeddings import LangChainBedrockEmbeddings

# Set up logging
logger = logging.getLogger(__name__)

app = FastAPI()

# Input schema
class QueryRequest(BaseModel):
    query: str
    index_id: str
    top_k: int = 5
    use_bedrock: bool = True  # Flag to toggle between Bedrock and Ollama embeddings

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

# Get embeddings based on configuration
def get_embeddings(use_bedrock=True):
    """
    Get the appropriate embeddings model based on configuration.
    
    Args:
        use_bedrock: Whether to use AWS Bedrock Titan Text Embeddings V2 (True) or Ollama (False)
        
    Returns:
        An embeddings model instance
    """
    if use_bedrock:
        logger.info("Using AWS Bedrock Titan Text Embeddings V2 for RAG")
        return LangChainBedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2",
            region_name=os.getenv("AWS_REGION", "ap-southeast-2")
        )
    else:
        logger.info("Using Ollama embeddings for RAG")
        return OllamaEmbeddings(model="tinyllama:latest")

# RAG pipeline
def rag_query(query: str, index_id: str, top_k: int = 5, use_bedrock: bool = True):
    # Get documents from Kendra
    docs = query_kendra(query, index_id, top_k)
    documents = [Document(page_content=d) for d in docs]

    # Split documents into chunks
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(documents)

    # Get embeddings based on configuration
    embeddings = get_embeddings(use_bedrock)
    
    # Create vector store
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    
    # Use Ollama for the LLM
    llm = Ollama(model="tinyllama:latest")

    # Create and run the RAG chain
    chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())
    return chain.run(query)

# API endpoint
@app.post("/rag/")
async def rag_handler(payload: QueryRequest):
    result = rag_query(
        payload.query, 
        payload.index_id, 
        payload.top_k,
        payload.use_bedrock
    )
    return {"query": payload.query, "result": result}
