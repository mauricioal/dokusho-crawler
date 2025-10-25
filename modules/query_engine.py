"""Module for querying indexed LinkedIn profile data."""

import logging
from typing import Any, Dict, Optional

from llama_index.core import VectorStoreIndex, PromptTemplate

from modules.llm_interface import create_watsonx_llm
import config

logger = logging.getLogger(__name__)

def generate_summary(index: VectorStoreIndex) -> str:
    """Generates a summary of a provided webpage based on its content.
    Args:
        index: VectorStoreIndex containing the webpage data.   
    Returns:
        String containing the summary of the webpage.
    """
    try:
        # Create LLM for generating summary
        watsonx_llm = create_watsonx_llm(
            temperature=0.0,
            max_new_tokens=500,
            decoding_method="sample"
        )
        
        # Create prompt template
        summary_prompt = PromptTemplate(template=config.WEBPAGE_SUMMARY_TEMPLATE)
        
        # Create query engine
        query_engine = index.as_query_engine(
            streaming=False,
            similarity_top_k=config.SIMILARITY_TOP_K,
            llm=watsonx_llm,
            text_qa_template=summary_prompt
        )
        
        # Execute the query
        query = "Provide a concise summary of the content of this webpage."
        response = query_engine.query(query)
        
        # Return the summary
        return response.response
    except Exception as e:
        logger.error(f"Error in generate_summary: {e}")
        return "Failed to generate summary."

def answer_user_query(index: VectorStoreIndex, user_query: str) -> Any:
    """Answers the user's question using the vector database and the LLM.
    
    Args:
        index: VectorStoreIndex containing the extracted data.
        user_query: The user's question.
        
    Returns:
        Response object containing the answer to the user's question.
    """
    try:
        # Create LLM for answering questions
        watsonx_llm = create_watsonx_llm(
            temperature=0.0,
            max_new_tokens=250,
            decoding_method="greedy"
        )
        
        # Create prompt template
        question_prompt = PromptTemplate(template=config.USER_QUESTION_TEMPLATE)
        
        # Retrieve relevant nodes
        base_retriever = index.as_retriever(similarity_top_k=config.SIMILARITY_TOP_K)
        source_nodes = base_retriever.retrieve(user_query)
        
        # Build context string
        context_str = "\n\n".join([node.node.get_text() for node in source_nodes])
        
        # Create query engine
        query_engine = index.as_query_engine(
            streaming=False,
            similarity_top_k=config.SIMILARITY_TOP_K,
            llm=watsonx_llm,
            text_qa_template=question_prompt
        )
        
        # Execute the query
        answer = query_engine.query(user_query)
        return answer
    except Exception as e:
        logger.error(f"Error in answer_user_query: {e}")
        return "Failed to get an answer."

def generate_story_from_vocabulary(jlpt_level: str, vocabulary_list: str, max_tokens: int = 3000) -> str:
    """
    Generate a simple Japanese story using user's mastered vocabulary.
    
    Args:
        jlpt_level: User's JLPT level (e.g., "N5", "N4")
        vocabulary_list: Comma-separated list of mastered vocabulary
        max_tokens: Maximum tokens for story generation
        
    Returns:
        Generated story in Japanese
    """
    try:
        # Create LLM for story generation
        watsonx_llm = create_watsonx_llm(
            temperature=0.7,  # Higher temperature for creative story
            max_new_tokens=max_tokens,
            decoding_method="sample"
        )
        
        # Format the prompt
        story_prompt = config.STORY_GENERATION_TEMPLATE.format(
            jlpt_level=jlpt_level,
            vocabulary_list=vocabulary_list
        )
        
        # Generate story directly using LLM
        response = watsonx_llm.complete(story_prompt)
        
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error in generate_story_from_vocabulary: {e}")
        return "Failed to generate story."