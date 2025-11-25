"""Module for persisting Renshuu data to SQLite database."""

import sqlite3
import json
import logging
import os
from typing import Optional, List, Dict, Any, Type
from datetime import datetime

from modules.renshuu_extraction import UserProfile, VocabularyTerm, KanjiTerm, GrammarTerm

logger = logging.getLogger(__name__)

DB_FILE = "renshuu_data.db"

def init_db(db_path: str = DB_FILE):
    """Initialize the database with necessary tables."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                real_name TEXT,
                level_progress_json TEXT,
                last_updated TIMESTAMP
            )
        """)
        
        # Create vocabulary_terms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary_terms (
                id TEXT,
                user_id TEXT,
                data_json TEXT,
                PRIMARY KEY (id, user_id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create kanji_terms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kanji_terms (
                id TEXT,
                user_id TEXT,
                data_json TEXT,
                PRIMARY KEY (id, user_id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create grammar_terms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grammar_terms (
                id TEXT,
                user_id TEXT,
                data_json TEXT,
                PRIMARY KEY (id, user_id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {db_path}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def save_user_profile(user_profile: UserProfile, db_path: str = DB_FILE):
    """Save user profile and all terms to the database."""
    if not user_profile:
        return
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Save user info
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, real_name, level_progress_json, last_updated)
            VALUES (?, ?, ?, ?)
        """, (
            user_profile.id,
            user_profile.real_name,
            json.dumps(user_profile.level_progress_percs),
            datetime.now()
        ))
        
        # Save terms
        _save_terms(cursor, user_profile.id, user_profile.vocabulary_terms, "vocabulary_terms")
        _save_terms(cursor, user_profile.id, user_profile.kanji_terms, "kanji_terms")
        _save_terms(cursor, user_profile.id, user_profile.grammar_terms, "grammar_terms")
        
        conn.commit()
        conn.close()
        logger.info(f"User profile {user_profile.id} saved to database")
    except Exception as e:
        logger.error(f"Error saving user profile: {e}")

def _save_terms(cursor, user_id: str, terms: List[Any], table_name: str):
    """Helper to save a list of terms."""
    if not terms:
        return
        
    # Clear existing terms for this user in this table to avoid duplicates/stale data
    cursor.execute(f"DELETE FROM {table_name} WHERE user_id = ?", (user_id,))
    
    # Batch insert
    data_to_insert = []
    seen_ids = set()
    
    for term in terms:
        if term.id in seen_ids:
            continue
            
        seen_ids.add(term.id)
        data_to_insert.append((
            term.id,
            user_id,
            json.dumps(term.model_dump())
        ))
        
    cursor.executemany(f"""
        INSERT INTO {table_name} (id, user_id, data_json)
        VALUES (?, ?, ?)
    """, data_to_insert)
    
    logger.info(f"Saved {len(data_to_insert)} unique terms to {table_name} (filtered from {len(terms)} total)")

def get_user_profile(db_path: str = DB_FILE) -> Optional[UserProfile]:
    """Retrieve the most recently updated user profile from the database."""
    try:
        if not os.path.exists(db_path):
            return None
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the most recent user
        cursor.execute("SELECT id, real_name, level_progress_json FROM users ORDER BY last_updated DESC LIMIT 1")
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
            
        user_id, real_name, level_progress_json = row
        
        # Reconstruct UserProfile
        user_profile = UserProfile(
            id=user_id,
            real_name=real_name,
            level_progress_percs=json.loads(level_progress_json)
        )
        
        # Load terms
        user_profile.vocabulary_terms = _get_terms(cursor, user_id, "vocabulary_terms", VocabularyTerm)
        user_profile.kanji_terms = _get_terms(cursor, user_id, "kanji_terms", KanjiTerm)
        user_profile.grammar_terms = _get_terms(cursor, user_id, "grammar_terms", GrammarTerm)
        
        conn.close()
        logger.info(f"Loaded user profile {user_id} from database")
        return user_profile
        
    except Exception as e:
        logger.error(f"Error loading user profile: {e}")
        return None

def _get_terms(cursor, user_id: str, table_name: str, term_class: Type[Any]) -> List[Any]:
    """Helper to retrieve terms."""
    cursor.execute(f"SELECT data_json FROM {table_name} WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    
    terms = []
    for row in rows:
        try:
            term_data = json.loads(row[0])
            terms.append(term_class(**term_data))
        except Exception as e:
            logger.warning(f"Error parsing term in {table_name}: {e}")
            
    return terms
