"""
AWS Bedrock Embeddings module for RAG.
This module provides functionality to convert text to embeddings using AWS Bedrock's Titan Text Embeddings V2.
"""

import os
import json
import boto3
import logging
from typing import List, Dict, Any, Optional, Union

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BedrockEmbeddings:
    """
    A class to generate embeddings using AWS Bedrock's Titan Text Embeddings V2 model.
    """
    
    def __init__(
        self,
        model_id: str = "amazon.titan-embed-text-v2:0",
        region_name: Optional[str] = None,
        credentials_profile: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the BedrockEmbeddings class.
        
        Args:
            model_id: The model ID to use for embeddings (default: amazon.titan-embed-text-v2)
            region_name: AWS region name (default: from environment variable AWS_REGION or ap-southeast-2)
            credentials_profile: AWS credentials profile to use (optional)
            **kwargs: Additional parameters to pass to the boto3 client
        """
        self.model_id = model_id
        self.region_name = region_name or os.getenv("AWS_REGION", "ap-southeast-2")
        
        # Initialize the Bedrock client
        session_kwargs = {}
        if credentials_profile:
            session_kwargs["profile_name"] = credentials_profile
        
        session = boto3.Session(**session_kwargs)
        self.bedrock_client = session.client(
            service_name="bedrock-runtime",
            region_name=self.region_name,
            **kwargs
        )
        
        logger.info(f"Initialized BedrockEmbeddings with model_id={model_id} in region={self.region_name}")
    
    def embed_documents(self, texts: List[str], dimensions: int = 1024, normalize: bool = True) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.
        
        Args:
            texts: List of text documents to embed
            dimensions: Number of output dimensions (default: 1024)
            normalize: Whether to return the normalized embedding or not (default: True)
            
        Returns:
            List of embeddings, one for each document
        """
        return [self.embed_query(text, dimensions, normalize) for text in texts]
    
    def embed_query(self, text: str, dimensions: int = 1024, normalize: bool = True) -> List[float]:
        """
        Generate embeddings for a single query text.
        
        Args:
            text: The text to embed
            dimensions: Number of output dimensions (default: 1024)
            normalize: Whether to return the normalized embedding or not (default: True)
            
        Returns:
            The embedding vector as a list of floats
        """
        try:
            # Prepare the request body for Titan Text Embeddings V2
            # According to AWS docs and examples, we need to include dimensions and normalize
            request_body = json.dumps({
                "inputText": text,
                "dimensions": dimensions,
                "normalize": normalize
            })
            
            logger.info(f"Invoking model {self.model_id} in region {self.region_name}")
            
            # Invoke the model
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=request_body
            )
            
            # Parse the response
            response_body_bytes = response.get("body").read()
            response_body = json.loads(response_body_bytes)
            
            # Log response for debugging
            logger.info(f"Response received with keys: {list(response_body.keys())}")
            
            # The embedding is in the 'embedding' field for Titan Text Embeddings V2
            if "embedding" in response_body:
                # Standard format for Titan Text Embeddings V2
                embedding = response_body.get("embedding")
                logger.info(f"Found embedding with length: {len(embedding)}")
                return embedding
            elif "embeddings" in response_body:
                # Alternative format that might be used
                embedding = response_body.get("embeddings")[0]
                logger.info(f"Found embeddings array with length: {len(embedding)}")
                return embedding
            else:
                # Log the full response for debugging
                logger.error(f"Unexpected response format. Response keys: {list(response_body.keys())}")
                # Print a sample of the response for debugging
                sample = str(response_body)[:200] + "..." if len(str(response_body)) > 200 else str(response_body)
                logger.error(f"Response sample: {sample}")
                raise ValueError(f"Could not find embeddings in response. Keys: {list(response_body.keys())}")
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

# Create a LangChain compatible embeddings class
class LangChainBedrockEmbeddings:
    """
    A LangChain compatible embeddings class for AWS Bedrock's Titan Text Embeddings V2.
    """
    
    def __init__(
        self,
        model_id: str = "amazon.titan-embed-text-v2",
        region_name: Optional[str] = None,
        credentials_profile: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the LangChainBedrockEmbeddings class.
        
        Args:
            model_id: The model ID to use for embeddings (default: amazon.titan-embed-text-v2)
            region_name: AWS region name (default: from environment variable AWS_REGION or ap-southeast-2)
            credentials_profile: AWS credentials profile to use (optional)
            **kwargs: Additional parameters to pass to the boto3 client
        """
        self.bedrock_embeddings = BedrockEmbeddings(
            model_id=model_id,
            region_name=region_name,
            credentials_profile=credentials_profile,
            **kwargs
        )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.
        
        Args:
            texts: List of text documents to embed
            
        Returns:
            List of embeddings, one for each document
        """
        return self.bedrock_embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embeddings for a single query text.
        
        Args:
            text: The text to embed
            
        Returns:
            The embedding vector as a list of floats
        """
        return self.bedrock_embeddings.embed_query(text)