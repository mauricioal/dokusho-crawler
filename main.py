"""Main script for running the Icebreaker Bot."""

import sys
import time
import logging
import argparse

from modules.renshuu_extraction import UserProfile, VocabularyTerm, KanjiTerm, GrammarTerm, extract_user_profile, extract_study_terms, create_mock_user_profile
from modules.data_processing import fetch_webpage_content, split_webpage_data, create_vector_database, verify_embeddings
from modules.query_engine import generate_summary, answer_user_query, generate_story_from_vocabulary
from typing import Dict, Any, Optional
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def extract_user_learning_data(user_profile: UserProfile) -> tuple[str, str, int]:
    """
    Extract JLPT level and mastered vocabulary from user profile.
    
    Returns:
        tuple: (jlpt_level, vocabulary_string, vocab_count)
    """
    # Determine JLPT level (minimum level with 50%+ progress)
    jlpt_level = "N5"  # default
    for level in range(1, 6):
        level_key = f"n{level}"
        vocab_progress = user_profile.level_progress_percs.get("vocab", {})
        if vocab_progress.get(level_key, 0) >= 30:
            jlpt_level = f"N{level}"
            break
    
    # Extract mastered vocabulary (50%+ mastery)
    mastered_vocab = []
    for term in user_profile.vocabulary_terms:
        raw = term.user_data.get("mastery_avg_perc", 0)
        try:
            mastery = float(str(raw).strip().rstrip('%')) if raw is not None else 0.0
        except (ValueError, TypeError):
            mastery = 0.0
        if mastery >= 50:
            vocab_entry = f"{term.kanji_full} ({term.hiragana_full})"
            mastered_vocab.append(vocab_entry)
    
    # Limit to top 100 most mastered terms (option to include all)
    vocab_list = mastered_vocab#[:100]
    vocabulary_string = ", ".join(vocab_list)
    
    return jlpt_level, vocabulary_string, len(mastered_vocab)

def process_webpage(webpage_url: str):
    """
    Processes a general webpage URL, extracts data from the page, and interacts with the user.

    Args:
        webpage_url: The webpage URL to extract data from.
        api_key: ProxyCurl API key. Not used in this function but kept for consistency.
        mock: If True, indicates mock processing. Not used in this function but kept for consistency.
    """
    try:
        # Extract the webpage data
        webpage_data = fetch_webpage_content(webpage_url)

          # Split the data into nodes
        nodes = split_webpage_data(webpage_data)
        
        # Store in vector database
        vectordb_index = create_vector_database(nodes)
        
        if not vectordb_index:
            logger.error("Failed to create vector database.")
            return
        
        # Verify embeddings
        if not verify_embeddings(vectordb_index):
            logger.warning("Some embeddings may be missing or invalid.")
        
        # Generate and display the initial facts
        initial_facts = generate_summary(vectordb_index)
        
        print("\nHere is a summary of this webpage:")
        print(initial_facts)
        
        # Start the chatbot interface
        chatbot_interface(vectordb_index)
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")

def chatbot_interface(index):
    """
    Provides a simple chatbot interface for user interaction.
    
    Args:
        index: VectorStoreIndex containing the webpage data.
    """
    print("\nYou can now ask more in-depth questions about this webpage. Type 'exit', 'quit', or 'bye' to quit.")
    
    while True:
        user_query = input("You: ")
        if user_query.lower() in ['exit', 'quit', 'bye']:
            print("Bot: Goodbye!")
            break
        
        print("Bot is typing...", end='')
        sys.stdout.flush()
        time.sleep(1)  # Simulate typing delay
        print('\r', end='')
        
        response = answer_user_query(index, user_query)
        print(f"Bot: {response.response.strip()}\n")

def main():
    """Main function to run the Icebreaker Bot."""
    parser = argparse.ArgumentParser(description='Dokusho Crawler Bot - Japanese Webpage Analyzer')
    parser.add_argument('--url', type=str, help='Webpage URL')
    parser.add_argument('--api-key', type=str, help='Renshuu API key')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of API')
    parser.add_argument('--model', type=str, help='LLM model to use (e.g., "ibm/granite-3-2-8b-instruct")')
    
    args = parser.parse_args()
    
    if args.model:
        from modules.llm_interface import change_llm_model
        change_llm_model(args.model)
    
    # process_webpage("https://kids.gakken.co.jp/kagaku/kagaku110/weatherdefinition20240405/")

    # Extract Renshuu user profile
    print("\n=== Renshuu User Profile ===")
    user_profile = extract_user_profile(config.RENSHUU_API_KEY)
    if user_profile:
        print(f"User ID: {user_profile.id}")
        print(f"Real Name: {user_profile.real_name}")
        print(f"Level Progress: {user_profile.level_progress_percs}")
        
        # Extract and populate terms
        user_profile = extract_study_terms(config.RENSHUU_API_KEY, user_profile)
        
        print(f"\nVocabulary terms: {len(user_profile.vocabulary_terms)}")
        print(f"Kanji terms: {len(user_profile.kanji_terms)}")
        print(f"Grammar terms: {len(user_profile.grammar_terms)}")
        
        # Show sample terms from each category
        if user_profile.vocabulary_terms:
            print(f"\nSample vocabulary term: {user_profile.vocabulary_terms[0].kanji_full} ({user_profile.vocabulary_terms[0].hiragana_full})")
        if user_profile.kanji_terms:
            print(f"Sample kanji term: {user_profile.kanji_terms[0].kanji} - {user_profile.kanji_terms[0].definition}")
        if user_profile.grammar_terms:
            print(f"Sample grammar term: {user_profile.grammar_terms[0].title_japanese} ({user_profile.grammar_terms[0].title_english})")
        
        # Generate a story based on user's vocabulary
        print("\n=== Generating Story ===")
        jlpt_level, vocab_string, total_vocab = extract_user_learning_data(user_profile)
        print(f"Detected JLPT Level: {jlpt_level}")
        print(f"Total mastered vocabulary: {total_vocab}")
        print(f"Using top 100 terms for story generation...\n")

        if vocab_string:
            story = generate_story_from_vocabulary(jlpt_level, vocab_string)
            print("Generated Story:")
            print(story)
        else:
            print("No mastered vocabulary found. Cannot generate story.")
    else:
        print("Using mock data for demonstration...")
        user_profile = create_mock_user_profile()
        print(f"Mock User ID: {user_profile.id}")
        print(f"Mock Real Name: {user_profile.real_name}")
        print(f"Mock Level Progress: {user_profile.level_progress_percs}")
        print(f"\nMock Vocabulary terms: {len(user_profile.vocabulary_terms)}")
        print(f"Mock Kanji terms: {len(user_profile.kanji_terms)}")
        print(f"Mock Grammar terms: {len(user_profile.grammar_terms)}")
        
        # Generate a story based on mock user's vocabulary
        print("\n=== Generating Story ===")
        jlpt_level, vocab_string, total_vocab = extract_user_learning_data(user_profile)
        print(f"Detected JLPT Level: {jlpt_level}")
        print(f"Total mastered vocabulary: {total_vocab}")
        print(f"Using top 100 terms for story generation...\n")

        if vocab_string:
            story = generate_story_from_vocabulary(jlpt_level, vocab_string)
            print("Generated Story:")
            print(story)
        else:
            print("No mastered vocabulary found. Cannot generate story.")

if __name__ == "__main__":
    main()