"""
Example of using AWS Bedrock Titan Text Embeddings V2 for semantic search.
"""

import numpy as np
from typing import List, Dict, Tuple
from .bedrock_embeddings import BedrockEmbeddings

class SemanticSearch:
    """
    A simple semantic search implementation using AWS Bedrock embeddings.
    """
    
    def __init__(self):
        """Initialize the semantic search with AWS Bedrock embeddings."""
        self.embeddings = BedrockEmbeddings()
        self.documents = []
        self.document_embeddings = []
    
    def add_documents(self, documents: List[str]) -> None:
        """
        Add documents to the search index.
        
        Args:
            documents: List of text documents to add
        """
        self.documents.extend(documents)
        
        # Generate embeddings for the documents
        new_embeddings = self.embeddings.embed_documents(documents)
        self.document_embeddings.extend(new_embeddings)
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Search for documents similar to the query.
        
        Args:
            query: The search query
            top_k: Number of top results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if not self.documents:
            return []
        
        # Generate embedding for the query
        query_embedding = self.embeddings.embed_query(query)
        
        # Calculate cosine similarity between query and all documents
        similarities = []
        for doc_embedding in self.document_embeddings:
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append(similarity)
        
        # Get the indices of the top_k most similar documents
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return the top_k documents and their similarity scores
        results = []
        for idx in top_indices:
            results.append((self.documents[idx], similarities[idx]))
        
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (between -1 and 1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        return dot_product / (norm1 * norm2)

# Example usage
if __name__ == "__main__":
    # Sample documents
    documents = [
        "AWS Bedrock is a fully managed service that offers a choice of high-performing foundation models.",
        "Amazon S3 is an object storage service offering industry-leading scalability, data availability, security, and performance.",
        "Amazon EC2 provides secure and resizable compute capacity in the cloud.",
        "AWS Lambda lets you run code without provisioning or managing servers.",
        "Amazon DynamoDB is a key-value and document database that delivers single-digit millisecond performance at any scale."
    ]
    
    # Create semantic search
    search = SemanticSearch()
    
    # Add documents
    search.add_documents(documents)
    
    # Search for similar documents
    query = "Which AWS service provides serverless computing?"
    results = search.search(query, top_k=2)
    
    print(f"Query: {query}")
    print("Top results:")
    for doc, score in results:
        print(f"- Score: {score:.4f}, Document: {doc}")