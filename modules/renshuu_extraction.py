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


class StudyTerm(BaseModel):
    """Study term model for Renshuu data."""
    id: str
    title_english: str = ""
    title_japanese: str = ""
    meaning: Dict[str, str] = {}
    meaning_long: Dict[str, str] = {}
    user_data: Dict[str, Any] = {}
    url: str = ""


class StudyTermsList(BaseModel):
    """Study terms list model for Renshuu data."""
    terms: List[StudyTerm]


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
        }
    )


def create_mock_study_terms() -> StudyTermsList:
    """Create mock study terms data for testing purposes.
    
    Returns:
        StudyTermsList with sample data.
    """
    return StudyTermsList(
        terms=[
            StudyTerm(
                id="280",
                title_english="Question",
                title_japanese="質問",
                meaning={"spa": "question, inquiry, enquiry"},
                meaning_long={"spa": "A question or inquiry"},
                user_data={
                    "correct_count": 21,
                    "missed_count": 0,
                    "mastery_avg_perc": "44"
                },
                url="https://www.renshuu.org/grammar/280"
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


def extract_study_terms(api_key: str) -> Optional[StudyTermsList]:
    """Extract study terms data from Renshuu API.
    
    Args:
        api_key: Bearer token for Renshuu API authentication.
    
    Returns:
        StudyTermsList object or None if extraction fails.
    """
    start_time = time.time()
    
    try:
        logger.info("Starting to extract Renshuu study terms...")
        
        # Set up headers
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # First, get all schedules
        schedules_endpoint = "https://api.renshuu.org/v1/schedule"
        logger.info(f"Fetching schedules at {time.time() - start_time:.2f} seconds...")
        
        schedules_response = requests.get(schedules_endpoint, headers=headers, timeout=10)
        
        if schedules_response.status_code != 200:
            logger.error(f"Failed to retrieve schedules. Status code: {schedules_response.status_code}")
            logger.error(f"Response: {schedules_response.text}")
            return None
        
        try:
            schedules_data = schedules_response.json()
            logger.info(f"Raw schedules response: {schedules_data}")
            
            # Handle different response formats
            if isinstance(schedules_data, list):
                schedules = schedules_data
            elif isinstance(schedules_data, dict):
                # Check if schedules are nested in a property
                if 'schedules' in schedules_data:
                    schedules = schedules_data['schedules']
                elif 'data' in schedules_data:
                    schedules = schedules_data['data']
                else:
                    schedules = []
                    logger.warning(f"Unexpected response format: {schedules_data}")
            else:
                schedules = []
                logger.warning(f"Unexpected response type: {type(schedules_data)}")
                
        except ValueError as e:
            logger.error(f"Error parsing schedules JSON response: {e}")
            logger.error(f"Raw response text: {schedules_response.text}")
            return None
        
        logger.info(f"Found {len(schedules)} schedules")
        
        # Aggregate all terms from all schedules
        all_terms = []
        
        for schedule in schedules:
            schedule_id = schedule.get("id")
            schedule_name = schedule.get("name", "Unknown")
            total_terms = schedule.get("terms", {}).get("total_count", 0)
            studied_terms = schedule.get("terms", {}).get("studied_count", 0)
            
            if not schedule_id:
                logger.warning("Schedule missing ID, skipping")
                continue
            
            logger.info(f"Processing schedule '{schedule_name}' (ID: {schedule_id}) - Total: {total_terms}, Studied: {studied_terms}")
            
            # Get terms for this schedule
            terms_endpoint = f"https://api.renshuu.org/v1/schedule/{schedule_id}/list"
            logger.info(f"Fetching terms for schedule {schedule_id} at {time.time() - start_time:.2f} seconds...")
            
            terms_response = requests.get(terms_endpoint, headers=headers, timeout=10)
            
            if terms_response.status_code == 200:
                try:
                    terms_data = terms_response.json()
                    logger.info(f"Raw terms response for schedule {schedule_id}: {terms_data}")
                    
                    # Handle different response formats
                    if 'contents' in terms_data and 'terms' in terms_data['contents']:
                        terms = terms_data['contents']['terms']
                        # Check pagination info
                        if 'total_pg' in terms_data['contents']:
                            total_pages = terms_data['contents']['total_pg']
                            current_page = terms_data['contents']['pg']
                            logger.info(f"Schedule {schedule_id}: Page {current_page}/{total_pages}, {len(terms)} terms on this page")
                            
                            # If there are multiple pages, fetch all of them
                            if total_pages > 1:
                                logger.info(f"Schedule {schedule_id} has {total_pages} pages - fetching all pages...")
                                
                                # Convert current page terms
                                for term_data in terms:
                                    try:
                                        study_term = StudyTerm(
                                            id=term_data.get("id", ""),
                                            title_english=term_data.get("title_english", ""),
                                            title_japanese=term_data.get("title_japanese", ""),
                                            meaning=term_data.get("meaning", {}),
                                            meaning_long=term_data.get("meaning_long", {}),
                                            user_data=term_data.get("user_data", {}),
                                            url=term_data.get("url", "")
                                        )
                                        all_terms.append(study_term)
                                    except Exception as e:
                                        logger.warning(f"Error creating StudyTerm from data: {e}")
                                        continue
                                
                                # Fetch remaining pages
                                for page in range(2, total_pages + 1):
                                    page_endpoint = f"https://api.renshuu.org/v1/schedule/{schedule_id}/list?pg={page}"
                                    logger.info(f"Fetching page {page}/{total_pages} for schedule {schedule_id}...")
                                    
                                    page_response = requests.get(page_endpoint, headers=headers, timeout=10)
                                    
                                    if page_response.status_code == 200:
                                        try:
                                            page_data = page_response.json()
                                            if 'contents' in page_data and 'terms' in page_data['contents']:
                                                page_terms = page_data['contents']['terms']
                                                logger.info(f"Page {page}: {len(page_terms)} terms")
                                                
                                                for term_data in page_terms:
                                                    try:
                                                        study_term = StudyTerm(
                                                            id=term_data.get("id", ""),
                                                            title_english=term_data.get("title_english", ""),
                                                            title_japanese=term_data.get("title_japanese", ""),
                                                            meaning=term_data.get("meaning", {}),
                                                            meaning_long=term_data.get("meaning_long", {}),
                                                            user_data=term_data.get("user_data", {}),
                                                            url=term_data.get("url", "")
                                                        )
                                                        all_terms.append(study_term)
                                                    except Exception as e:
                                                        logger.warning(f"Error creating StudyTerm from data: {e}")
                                                        continue
                                            else:
                                                logger.warning(f"Unexpected page response format for schedule {schedule_id}, page {page}")
                                        except ValueError as e:
                                            logger.error(f"Error parsing page {page} JSON response for schedule {schedule_id}: {e}")
                                            continue
                                    else:
                                        logger.error(f"Failed to retrieve page {page} for schedule {schedule_id}. Status code: {page_response.status_code}")
                                        continue
                                
                                logger.info(f"Completed fetching all {total_pages} pages for schedule {schedule_id}")
                            else:
                                # Single page - convert terms normally
                                for term_data in terms:
                                    try:
                                        study_term = StudyTerm(
                                            id=term_data.get("id", ""),
                                            title_english=term_data.get("title_english", ""),
                                            title_japanese=term_data.get("title_japanese", ""),
                                            meaning=term_data.get("meaning", {}),
                                            meaning_long=term_data.get("meaning_long", {}),
                                            user_data=term_data.get("user_data", {}),
                                            url=term_data.get("url", "")
                                        )
                                        all_terms.append(study_term)
                                    except Exception as e:
                                        logger.warning(f"Error creating StudyTerm from data: {e}")
                                        continue
                        else:
                            # No pagination info - convert terms normally
                            for term_data in terms:
                                try:
                                    study_term = StudyTerm(
                                        id=term_data.get("id", ""),
                                        title_english=term_data.get("title_english", ""),
                                        title_japanese=term_data.get("title_japanese", ""),
                                        meaning=term_data.get("meaning", {}),
                                        meaning_long=term_data.get("meaning_long", {}),
                                        user_data=term_data.get("user_data", {}),
                                        url=term_data.get("url", "")
                                    )
                                    all_terms.append(study_term)
                                except Exception as e:
                                    logger.warning(f"Error creating StudyTerm from data: {e}")
                                    continue
                    elif 'terms' in terms_data:
                        terms = terms_data['terms']
                        for term_data in terms:
                            try:
                                study_term = StudyTerm(
                                    id=term_data.get("id", ""),
                                    title_english=term_data.get("title_english", ""),
                                    title_japanese=term_data.get("title_japanese", ""),
                                    meaning=term_data.get("meaning", {}),
                                    meaning_long=term_data.get("meaning_long", {}),
                                    user_data=term_data.get("user_data", {}),
                                    url=term_data.get("url", "")
                                )
                                all_terms.append(study_term)
                            except Exception as e:
                                logger.warning(f"Error creating StudyTerm from data: {e}")
                                continue
                    else:
                        terms = []
                        logger.warning(f"Unexpected terms response format for schedule {schedule_id}: {terms_data}")
                    
                    logger.info(f"Added {len(terms)} terms from schedule {schedule_id}")
                    if len(terms) == 0:
                        logger.warning(f"Schedule {schedule_id} returned 0 terms - this might indicate an issue")
                    
                except ValueError as e:
                    logger.error(f"Error parsing terms JSON response for schedule {schedule_id}: {e}")
                    continue
            else:
                logger.warning(f"Failed to retrieve terms for schedule {schedule_id}. Status code: {terms_response.status_code}")
                continue
        
        logger.info(f"Total terms extracted: {len(all_terms)} at {time.time() - start_time:.2f} seconds")
        
        # Create StudyTermsList model
        study_terms_list = StudyTermsList(terms=all_terms)
        
        logger.info("Study terms extracted successfully")
        return study_terms_list
        
    except Exception as e:
        logger.error(f"Error in extract_study_terms: {e}")
        return None
