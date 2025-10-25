"""
Icebreaker Bot modules package.

This package contains the following modules:
- data_processing: Functions for processing and indexing data
- llm_interface: Functions for interfacing with IBM watsonx.ai LLMs
- query_engine: Functions for querying indexed data
- renshuu_extraction: Functions for extracting Renshuu user data
"""

from modules.data_processing import create_vector_database, verify_embeddings, fetch_webpage_content, split_webpage_data
from modules.llm_interface import create_watsonx_embedding, create_watsonx_llm, change_llm_model
from modules.query_engine import answer_user_query, generate_summary, generate_story_from_vocabulary
from modules.renshuu_extraction import UserProfile, VocabularyTerm, KanjiTerm, GrammarTerm, extract_user_profile, extract_study_terms, create_mock_user_profile