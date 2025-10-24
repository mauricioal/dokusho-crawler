"""Module for processing LinkedIn profile data."""

import json
import logging
from typing import Dict, List, Any, Optional

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.web import SimpleWebPageReader

from modules.llm_interface import create_watsonx_embedding
import config

logger = logging.getLogger(__name__)

def fetch_webpage_content(url: str) -> Document:
    """Fetch webpage content using SimpleWebPageReader.
    
    Args:
        url: The URL of the webpage to fetch.
    
    Returns:
        The content of the webpage as a string.
    """
    try:
        reader = SimpleWebPageReader()
        documents = reader.load_data(urls=[url])
        if documents:
            return documents[0]
        else:
            logger.warning(f"No content found at {url}")
            return ""
    except Exception as e:
        logger.error(f"Error fetching webpage content from {url}: {e}")
        return ""
    
def split_webpage_data(webpage_data: Document) -> List:
    """Splits the webpage Document into nodes.
    
    Args:
        webpage_data: Document object containing the webpage content.
        
    Returns:
        List of document nodes.
    """
    try:
        # Split the document into nodes using SentenceSplitter
        splitter = SentenceSplitter(chunk_size=config.CHUNK_SIZE)
        nodes = splitter.get_nodes_from_documents([webpage_data])
        
        logger.info(f"Created {len(nodes)} nodes from webpage data")
        return nodes
    except Exception as e:
        logger.error(f"Error in split_webpage_data: {e}")
        return []

def create_vector_database(nodes: List) -> Optional[VectorStoreIndex]:
    """Stores the document chunks (nodes) in a vector database.
    
    Args:
        nodes: List of document nodes to be indexed.
        
    Returns:
        VectorStoreIndex or None if indexing fails.
    """
    try:
        # Get the embedding model
        embedding_model = create_watsonx_embedding()

        # Create a VectorStoreIndex from the nodes
        index = VectorStoreIndex(
            nodes=nodes,
            embed_model=embedding_model,
            show_progress=True
        )
        
        logger.info("Vector database created successfully")
        return index
    except Exception as e:
        logger.error(f"Error in create_vector_database: {e}")
        return None

def verify_embeddings(index: VectorStoreIndex) -> bool:
    """Verify that all nodes have been properly embedded.
    
    Args:
        index: VectorStoreIndex to verify.
        
    Returns:
        True if all embeddings are valid, False otherwise.
    """
    try:
        vector_store = index._storage_context.vector_store
        node_ids = list(index.index_struct.nodes_dict.keys())
        missing_embeddings = False

        for node_id in node_ids:
            embedding = vector_store.get(node_id)
            if embedding is None:
                logger.warning(f"Node ID {node_id} has a None embedding.")
                missing_embeddings = True
            else:
                logger.debug(f"Node ID {node_id} has a valid embedding.")
        
        if missing_embeddings:
            logger.warning("Some node embeddings are missing")
            return False
        else:
            logger.info("All node embeddings are valid")
            return True
    except Exception as e:
        logger.error(f"Error in verify_embeddings: {e}")
        return False