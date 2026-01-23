"""
Quote History Database Module

Manages a SQLite database to track previously used prayer quotes,
ensuring fresh quotes are generated for each devotional email.
"""

import sqlite3
import os
from datetime import datetime

# Database file location (same directory as this script)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quotes.db")


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_text TEXT UNIQUE NOT NULL,
            author TEXT,
            date_used TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def get_used_quotes():
    """
    Retrieve all previously used quotes from the database.
    
    Returns:
        List of tuples: [(quote_text, author), ...]
    """
    init_db()  # Ensure DB exists
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT quote_text, author FROM quotes ORDER BY date_used DESC")
    quotes = cursor.fetchall()
    
    conn.close()
    return quotes


def add_quotes(quotes_list):
    """
    Add new quotes to the database.
    
    Args:
        quotes_list: List of dicts with 'quote' and 'author' keys
                     e.g., [{'quote': '...', 'author': 'Name'}, ...]
    
    Returns:
        int: Number of quotes successfully added (duplicates are skipped)
    """
    init_db()  # Ensure DB exists
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = datetime.now().isoformat()[:10]  # YYYY-MM-DD
    added_count = 0
    
    for item in quotes_list:
        try:
            cursor.execute(
                "INSERT INTO quotes (quote_text, author, date_used) VALUES (?, ?, ?)",
                (item.get('quote', ''), item.get('author', 'Unknown'), today)
            )
            added_count += 1
        except sqlite3.IntegrityError:
            # Quote already exists (duplicate), skip it
            pass
    
    conn.commit()
    conn.close()
    
    return added_count


def get_quote_count():
    """Return the total number of quotes in the database."""
    init_db()  # Ensure DB exists
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM quotes")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count


def format_exclusion_list(max_quotes=50):
    """
    Format previously used quotes as a string for the AI prompt.
    
    Args:
        max_quotes: Maximum number of quotes to include (most recent first)
    
    Returns:
        str: Formatted list of quotes, or empty string if no history
    """
    quotes = get_used_quotes()
    
    if not quotes:
        return ""
    
    # Limit to max_quotes most recent
    quotes = quotes[:max_quotes]
    
    lines = []
    for quote_text, author in quotes:
        # Truncate long quotes for the prompt
        if len(quote_text) > 100:
            quote_text = quote_text[:100] + "..."
        lines.append(f'- "{quote_text}" - {author}')
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test
    init_db()
    print(f"Database initialized at: {DB_PATH}")
    print(f"Total quotes in database: {get_quote_count()}")
