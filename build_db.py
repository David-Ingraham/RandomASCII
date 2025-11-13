#!/usr/bin/env python3
"""
Database Builder for ASCII Art Collection
Scrapes asciiart.website and stores all artworks in SQLite database.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import sys
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def create_database(db_path="ascii_art.db"):
    """Create the SQLite database schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            artwork TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_category_id ON artworks(category_id)
    """)
    
    conn.commit()
    return conn


def fetch_category_links(base_url="https://asciiart.website/browse.php"):
    """Fetch all category links and names from the browse page."""
    print("Fetching categories...")
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching browse page: {e}", file=sys.stderr)
        sys.exit(1)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    categories = {}
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'cat.php?category_id=' in href:
            if not href.startswith('http'):
                href = f"https://asciiart.website/{href}"
            
            category_name = link.get_text(strip=True)
            if '(' in category_name:
                category_name = category_name.split('(')[0].strip()
            
            categories[category_name] = href
    
    print(f"Found {len(categories)} categories")
    return categories


def fetch_artworks_from_category(category_url):
    """Fetch all ASCII artworks from a category page."""
    try:
        response = requests.get(category_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching category: {e}", file=sys.stderr)
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    artworks = []
    pre_tags = soup.find_all('pre', class_='adu-artwork-pre')
    
    for pre in pre_tags:
        artwork_text = pre.get_text()
        if artwork_text.strip():
            artworks.append(artwork_text)
    
    return artworks


def build_database(db_path="ascii_art.db"):
    """Main function to scrape and build the database."""
    print("Creating database...")
    conn = create_database(db_path)
    cursor = conn.cursor()
    
    # Fetch all categories
    categories = fetch_category_links()
    
    total_artworks = 0
    
    for idx, (category_name, category_url) in enumerate(categories.items(), 1):
        print(f"\n[{idx}/{len(categories)}] Processing: {category_name}")
        
        # Insert category
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category_name,))
        cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
        category_id = cursor.fetchone()[0]
        
        # Fetch artworks
        artworks = fetch_artworks_from_category(category_url)
        print(f"  Found {len(artworks)} artworks")
        
        # Insert artworks
        for artwork in artworks:
            cursor.execute(
                "INSERT INTO artworks (category_id, artwork) VALUES (?, ?)",
                (category_id, artwork)
            )
        
        total_artworks += len(artworks)
        conn.commit()
        
        # Be nice to the server
        time.sleep(0.5)
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"Database build complete!")
    print(f"Total categories: {len(categories)}")
    print(f"Total artworks: {total_artworks}")
    print(f"Database saved to: {db_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        build_database()
    except KeyboardInterrupt:
        print("\n\nBuild interrupted by user.")
        sys.exit(1)

