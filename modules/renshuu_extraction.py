"""Module for extracting Renshuu user profile and study data."""

import time
import requests
import logging
from typing import Dict, List, Optional, Any

from pydantic import BaseModel

import config

logger = logging.getLogger(__name__)


class UserProfile(BaseModel):
    """User profile model for Renshuu data."""
    id: str
    real_name: str
    level_progress_percs: Dict[str, Dict[str, int]]
    vocabulary_terms: List['VocabularyTerm'] = []
    kanji_terms: List['KanjiTerm'] = []
    grammar_terms: List['GrammarTerm'] = []


class VocabularyTerm(BaseModel):
    """Vocabulary/Word term model."""
    id: str
    kanji_full: str = ""
    hiragana_full: str = ""
    edict_ent: Optional[str] = ""
    config: List[str] = []
    user_data: Dict[str, Any] = {}
    reibuns: str = ""
    pitch: List[str] = []
    typeofspeech: str = ""
    def_: List[str] = []  # 'def' is reserved, use 'def_'


class KanjiTerm(BaseModel):
    """Kanji term model."""
    id: str
    kanji: str
    scount: str = ""
    definition: str = ""
    onyomi: str = ""
    kunyomi: str = ""
    user_data: Dict[str, Any] = {}
    kanken: str = ""
    jlpt: str = ""
    radical_name: str = ""
    radical: str = ""


class GrammarTerm(BaseModel):
    """Grammar term model."""
    id: str
    title_english: str = ""
    title_japanese: str = ""
    user_data: Dict[str, Any] = {}
    meaning: Dict[str, str] = {}
    meaning_long: Dict[str, str] = {}
    url: str = ""


def _detect_schedule_type(terms: List[Dict[str, Any]]) -> str:
    """Detect schedule type by inspecting term structure.
    
    Returns: 'vocabulary', 'kanji', or 'grammar'
    """
    if not terms:
        return 'unknown'
    
    first_term = terms[0]
    
    # Check for kanji-specific fields
    if 'kanji' in first_term and 'onyomi' in first_term:
        return 'kanji'
    
    # Check for vocabulary-specific fields
    if 'kanji_full' in first_term and 'hiragana_full' in first_term:
        return 'vocabulary'
    
    # Check for grammar-specific fields
    if 'title_japanese' in first_term and 'url' in first_term:
        return 'grammar'
    
    return 'unknown'


def _create_vocabulary_term(term_data: Dict[str, Any]) -> Optional[VocabularyTerm]:
    """Create VocabularyTerm from raw data."""
    try:
        return VocabularyTerm(
            id=term_data.get("id", ""),
            kanji_full=term_data.get("kanji_full", ""),
            hiragana_full=term_data.get("hiragana_full", ""),
            edict_ent=term_data.get("edict_ent", ""),
            config=term_data.get("config", []),
            user_data=term_data.get("user_data", {}),
            reibuns=term_data.get("reibuns", ""),
            pitch=term_data.get("pitch", []),
            typeofspeech=term_data.get("typeofspeech", ""),
            def_=term_data.get("def", [])
        )
    except Exception as e:
        logger.warning(f"Error creating VocabularyTerm: {e}")
        return None


def _create_kanji_term(term_data: Dict[str, Any]) -> Optional[KanjiTerm]:
    """Create KanjiTerm from raw data."""
    try:
        return KanjiTerm(
            id=term_data.get("id", ""),
            kanji=term_data.get("kanji", ""),
            scount=term_data.get("scount", ""),
            definition=term_data.get("definition", ""),
            onyomi=term_data.get("onyomi", ""),
            kunyomi=term_data.get("kunyomi", ""),
            user_data=term_data.get("user_data", {}),
            kanken=term_data.get("kanken", ""),
            jlpt=term_data.get("jlpt", ""),
            radical_name=term_data.get("radical_name", ""),
            radical=term_data.get("radical", "")
        )
    except Exception as e:
        logger.warning(f"Error creating KanjiTerm: {e}")
        return None


def _create_grammar_term(term_data: Dict[str, Any]) -> Optional[GrammarTerm]:
    """Create GrammarTerm from raw data."""
    try:
        return GrammarTerm(
            id=term_data.get("id", ""),
            title_english=term_data.get("title_english", ""),
            title_japanese=term_data.get("title_japanese", ""),
            user_data=term_data.get("user_data", {}),
            meaning=term_data.get("meaning", {}),
            meaning_long=term_data.get("meaning_long", {}),
            url=term_data.get("url", "")
        )
    except Exception as e:
        logger.warning(f"Error creating GrammarTerm: {e}")
        return None


def create_mock_user_profile() -> UserProfile:
    """Create mock user profile data for testing purposes.
    
    Returns:
        UserProfile with sample data.
    """
    return UserProfile(
        id="1627619",
        real_name="ススワタリ",
        level_progress_percs={
            "vocab": {
                "n1": 0,
                "n2": 1,
                "n3": 6,
                "n4": 31,
                "n5": 100
            },
            "kanji": {
                "n1": 0,
                "n2": 0,
                "n3": 0,
                "n4": 100,
                "n5": 100
            },
            "grammar": {
                "n1": 0,
                "n2": 0,
                "n3": 2,
                "n4": 13,
                "n5": 100
            },
            "sent": {
                "n1": 0,
                "n2": 0,
                "n3": 0,
                "n4": 0,
                "n5": 0
            }
        },
        vocabulary_terms=[
            VocabularyTerm(
                id="280",
                kanji_full="質問",
                hiragana_full="しつもん",
                edict_ent="1320760",
                config=["JLPT N5", "News 12k", "Common 500"],
                user_data={"correct_count": 21, "missed_count": 0, "mastery_avg_perc": "44"},
                reibuns="質問があります。",
                pitch=["し⭧つもん"],
                typeofspeech="(noun/する verb)",
                def_=["question", "inquiry", "enquiry"]
            )
        ],
        kanji_terms=[
            KanjiTerm(
                id="2160",
                kanji="日",
                scount="4",
                definition="día, solar, Japón",
                onyomi="ニチ, ジツ",
                kunyomi="ひ, か",
                user_data={"correct_count": 15, "missed_count": 2, "mastery_avg_perc": "78"},
                kanken="10級",
                jlpt="N5",
                radical_name="日",
                radical="日"
            )
        ],
        grammar_terms=[
            GrammarTerm(
                id="539",
                title_english="amari ~ nai",
                title_japanese="あまり〜ない",
                user_data={"correct_count": 8, "missed_count": 1, "mastery_avg_perc": "65"},
                meaning={"spa": "no mucho", "eng": "not very"},
                meaning_long={"spa": "Se usa para expresar que algo no es muy...", "eng": "Used to express that something is not very..."},
                url="https://renshuu.org/grammar/539"
            )
        ]
    )


def extract_user_profile(api_key: str) -> Optional[UserProfile]:
    """Extract user profile data from Renshuu API.
    
    Args:
        api_key: Bearer token for Renshuu API authentication.
    
    Returns:
        UserProfile object or None if extraction fails.
    """
    start_time = time.time()
    
    try:
        logger.info("Starting to extract Renshuu user profile...")
        
        # Check if API key is provided
        if not api_key or api_key.strip() == "":
            logger.error("Renshuu API key is not provided or empty")
            return None
        
        # Set up the API endpoint and headers
        api_endpoint = "https://api.renshuu.org/v1/profile"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        logger.info(f"Sending API request to Renshuu profile endpoint at {time.time() - start_time:.2f} seconds...")
        
        # Send API request
        response = requests.get(api_endpoint, headers=headers, timeout=10)
        
        logger.info(f"Received response at {time.time() - start_time:.2f} seconds...")
        
        # Check if response is successful
        if response.status_code == 200:
            try:
                # Parse the JSON response
                data = response.json()
                
                # Create UserProfile model from response
                user_profile = UserProfile(
                    id=data.get("id", ""),
                    real_name=data.get("real_name", ""),
                    level_progress_percs=data.get("level_progress_percs", {})
                )
                
                logger.info("User profile extracted successfully")
                return user_profile
                
            except ValueError as e:
                logger.error(f"Error parsing JSON response: {e}")
                logger.error(f"Response content: {response.text[:200]}...")
                return None
        elif response.status_code == 401:
            logger.error("Authentication failed. Please check your Renshuu API key.")
            logger.error("To get a valid API key, visit: https://api.renshuu.org/docs/")
            return None
        else:
            logger.error(f"Failed to retrieve user profile. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error in extract_user_profile: {e}")
        return None


def _process_terms_from_response(terms_data: List[Dict[str, Any]]) -> tuple[str, List]:
    """Process terms and return (type, terms_list).
    
    Args:
        terms_data: List of raw term data from API.
    
    Returns:
        Tuple of (schedule_type, processed_terms_list).
    """
    schedule_type = _detect_schedule_type(terms_data)
    processed_terms = []
    
    for term_data in terms_data:
        if schedule_type == 'vocabulary':
            term = _create_vocabulary_term(term_data)
        elif schedule_type == 'kanji':
            term = _create_kanji_term(term_data)
        elif schedule_type == 'grammar':
            term = _create_grammar_term(term_data)
        else:
            logger.warning(f"Unknown schedule type: {schedule_type}")
            continue
            
        if term:
            processed_terms.append(term)
    
    return schedule_type, processed_terms


def _extract_terms_from_schedule(schedule_id: str, headers: Dict[str, str], start_time: float) -> tuple[str, List]:
    """Extract all terms from a single schedule, handling pagination.
    
    Args:
        schedule_id: ID of the schedule to extract terms from.
        headers: HTTP headers for API requests.
        start_time: Start time for logging.
    
    Returns:
        Tuple of (schedule_type, terms_list).
    """
    all_terms = []
    schedule_type = 'unknown'
    terms_endpoint = f"https://api.renshuu.org/v1/schedule/{schedule_id}/list"
    logger.info(f"Fetching terms for schedule {schedule_id} at {time.time() - start_time:.2f} seconds...")
    
    terms_response = requests.get(terms_endpoint, headers=headers, timeout=10)
    
    if terms_response.status_code != 200:
        logger.warning(f"Failed to retrieve terms for schedule {schedule_id}. Status code: {terms_response.status_code}")
        return all_terms
    
    try:
        terms_data = terms_response.json()
        logger.info(f"Raw terms response for schedule {schedule_id}: {terms_data}")
        
        # Handle different response formats
        if 'contents' in terms_data and 'terms' in terms_data['contents']:
            terms = terms_data['contents']['terms']
            pagination_info = terms_data['contents']
            
            # Check pagination info
            if 'total_pg' in pagination_info:
                total_pages = pagination_info['total_pg']
                current_page = pagination_info['pg']
                logger.info(f"Schedule {schedule_id}: Page {current_page}/{total_pages}, {len(terms)} terms on this page")
                
                # Process current page
                page_type, page_terms = _process_terms_from_response(terms)
                if schedule_type == 'unknown':
                    schedule_type = page_type
                all_terms.extend(page_terms)
                
                # Fetch remaining pages if any
                if total_pages > 1:
                    logger.info(f"Schedule {schedule_id} has {total_pages} pages - fetching all pages...")
                    for page in range(2, total_pages + 1):
                        page_terms = _fetch_terms_from_page(schedule_id, page, headers)
                        all_terms.extend(page_terms)
                    logger.info(f"Completed fetching all {total_pages} pages for schedule {schedule_id}")
            else:
                # No pagination info - process terms normally
                page_type, page_terms = _process_terms_from_response(terms)
                if schedule_type == 'unknown':
                    schedule_type = page_type
                all_terms.extend(page_terms)
                
        elif 'terms' in terms_data:
            # Alternative response format
            terms = terms_data['terms']
            page_type, page_terms = _process_terms_from_response(terms)
            if schedule_type == 'unknown':
                schedule_type = page_type
            all_terms.extend(page_terms)
        else:
            logger.warning(f"Unexpected terms response format for schedule {schedule_id}: {terms_data}")
        
        logger.info(f"Added {len(all_terms)} terms from schedule {schedule_id}")
        if len(all_terms) == 0:
            logger.warning(f"Schedule {schedule_id} returned 0 terms - this might indicate an issue")
            
    except ValueError as e:
        logger.error(f"Error parsing terms JSON response for schedule {schedule_id}: {e}")
    
    return schedule_type, all_terms


def _fetch_terms_from_page(schedule_id: str, page: int, headers: Dict[str, str]) -> List:
    """Fetch terms from a specific page of a schedule.
    
    Args:
        schedule_id: ID of the schedule.
        page: Page number to fetch.
        headers: HTTP headers for API requests.
    
    Returns:
        List of StudyTerm objects from the page.
    """
    page_endpoint = f"https://api.renshuu.org/v1/schedule/{schedule_id}/list?pg={page}"
    logger.info(f"Fetching page {page} for schedule {schedule_id}...")
    
    page_response = requests.get(page_endpoint, headers=headers, timeout=10)
    
    if page_response.status_code != 200:
        logger.error(f"Failed to retrieve page {page} for schedule {schedule_id}. Status code: {page_response.status_code}")
        return []
    
    try:
        page_data = page_response.json()
        if 'contents' in page_data and 'terms' in page_data['contents']:
            page_terms = page_data['contents']['terms']
            logger.info(f"Page {page}: {len(page_terms)} terms")
            _, page_terms = _process_terms_from_response(page_terms)
            return page_terms
        else:
            logger.warning(f"Unexpected page response format for schedule {schedule_id}, page {page}")
            return []
    except ValueError as e:
        logger.error(f"Error parsing page {page} JSON response for schedule {schedule_id}: {e}")
        return []


def _parse_schedules_response(schedules_response: requests.Response) -> List[Dict[str, Any]]:
    """Parse schedules response and extract schedules list.
    
    Args:
        schedules_response: HTTP response from schedules endpoint.
    
    Returns:
        List of schedule dictionaries.
    """
    try:
        schedules_data = schedules_response.json()
        logger.info(f"Raw schedules response: {schedules_data}")
        
        # Handle different response formats
        if isinstance(schedules_data, list):
            return schedules_data
        elif isinstance(schedules_data, dict):
            if 'schedules' in schedules_data:
                return schedules_data['schedules']
            elif 'data' in schedules_data:
                return schedules_data['data']
            else:
                logger.warning(f"Unexpected response format: {schedules_data}")
                return []
        else:
            logger.warning(f"Unexpected response type: {type(schedules_data)}")
            return []
            
    except ValueError as e:
        logger.error(f"Error parsing schedules JSON response: {e}")
        logger.error(f"Raw response text: {schedules_response.text}")
        return []


def extract_study_terms(api_key: str, user_profile: UserProfile) -> UserProfile:
    """Extract study terms and populate UserProfile.
    
    Args:
        api_key: Bearer token for Renshuu API authentication.
        user_profile: UserProfile to populate with terms.
    
    Returns:
        Updated UserProfile with terms populated.
    """
    start_time = time.time()
    
    try:
        logger.info("Starting to extract Renshuu study terms...")
        
        # Set up headers
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # First, get all schedules
        schedules_endpoint = "https://api.renshuu.org/v1/schedule"
        logger.info(f"Fetching schedules at {time.time() - start_time:.2f} seconds...")
        
        schedules_response = requests.get(schedules_endpoint, headers=headers, timeout=10)
        
        if schedules_response.status_code != 200:
            logger.error(f"Failed to retrieve schedules. Status code: {schedules_response.status_code}")
            logger.error(f"Response: {schedules_response.text}")
            return None
        
        schedules = _parse_schedules_response(schedules_response)
        logger.info(f"Found {len(schedules)} schedules")
        
        for schedule in schedules:
            schedule_id = schedule.get("id")
            schedule_name = schedule.get("name", "Unknown")
            total_terms = schedule.get("terms", {}).get("total_count", 0)
            studied_terms = schedule.get("terms", {}).get("studied_count", 0)
            
            if not schedule_id:
                logger.warning("Schedule missing ID, skipping")
                continue
            
            logger.info(f"Processing schedule '{schedule_name}' (ID: {schedule_id}) - Total: {total_terms}, Studied: {studied_terms}")
            
            # Extract terms from this schedule
            schedule_type, schedule_terms = _extract_terms_from_schedule(schedule_id, headers, start_time)
            
            # Add to appropriate list
            if schedule_type == 'vocabulary':
                user_profile.vocabulary_terms.extend(schedule_terms)
            elif schedule_type == 'kanji':
                user_profile.kanji_terms.extend(schedule_terms)
            elif schedule_type == 'grammar':
                user_profile.grammar_terms.extend(schedule_terms)
        
        logger.info(f"Total terms: {len(user_profile.vocabulary_terms)} vocab, "
                    f"{len(user_profile.kanji_terms)} kanji, "
                    f"{len(user_profile.grammar_terms)} grammar")
        
        logger.info("Study terms extracted successfully")
        return user_profile
        
    except Exception as e:
        logger.error(f"Error in extract_study_terms: {e}")
        return user_profile
