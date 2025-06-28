"""
Test script for AWS Bedrock Titan Text Embeddings V2.
This script can be run to test the connection to AWS Bedrock and generate embeddings.
"""

import os
import argparse
import logging
from bedrock_embeddings import BedrockEmbeddings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_bedrock_embeddings(text, region=None):
    """
    Test the Bedrock embeddings by generating embeddings for the given text.
    
    Args:
        text: The text to generate embeddings for
        region: AWS region to use (default: from environment variable AWS_REGION or us-east-1)
    """
    try:
        # Initialize the Bedrock embeddings
        embeddings = BedrockEmbeddings(region_name=region)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for text: '{text}'")
        embedding_vector = embeddings.embed_query(text)
        
        # Print the results
        logger.info(f"Successfully generated embeddings with {len(embedding_vector)} dimensions")
        logger.info(f"First 5 values: {embedding_vector[:5]}")
        
        return embedding_vector
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test AWS Bedrock Titan Text Embeddings V2")
    parser.add_argument("--text", type=str, default="Hello, world!", help="Text to generate embeddings for")
    parser.add_argument("--region", type=str, default=None, help="AWS region (default: from environment variable)")
    
    args = parser.parse_args()
    
    # Run the test
    test_bedrock_embeddings(args.text, args.region)