#!/usr/bin/env python3
"""
Add Dimensions to ASCII Art Database
Scrapes dimension data from asciiart.website and updates existing database.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import sys
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def add_dimension_columns(db_path="ascii_art.db"):
    """Add width and height columns to artworks table if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(artworks)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'width' not in columns:
        print("Adding width column...")
        cursor.execute("ALTER TABLE artworks ADD COLUMN width INTEGER")
    
    if 'height' not in columns:
        print("Adding height column...")
        cursor.execute("ALTER TABLE artworks ADD COLUMN height INTEGER")
    
    conn.commit()
    return conn


def fetch_category_links(base_url="https://asciiart.website/browse.php"):
    """Fetch all category links from the browse page."""
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


def fetch_artworks_with_dimensions(category_url):
    """Fetch artworks and their dimensions from a category page.
    
    Returns:
        list: List of tuples (artwork_text, width, height)
    """
    try:
        response = requests.get(category_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching category: {e}", file=sys.stderr)
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    artworks_data = []
    
    # Find all artwork containers
    artwork_containers = soup.find_all('div', class_='adu-artwork-display')
    
    for container in artwork_containers:
        # Get the artwork text from the pre tag
        pre_tag = container.find('pre', class_=lambda c: c and 'adu-artwork-pre' in c)
        if not pre_tag:
            continue
        
        artwork_text = pre_tag.get_text()
        if not artwork_text.strip():
            continue
        
        # Find the metadata section
        metadata = container.find('div', class_='adu-artwork-metadata')
        if not metadata:
            continue
        
        # Find the dimensions paragraph
        dimensions_p = None
        for p in metadata.find_all('p'):
            if 'Dimensions:' in p.get_text():
                dimensions_p = p
                break
        
        if not dimensions_p:
            continue
        
        # Parse dimensions (format: "Dimensions: 29 x 7")
        dimensions_text = dimensions_p.get_text()
        try:
            # Extract "29 x 7" part
            dims = dimensions_text.split(':')[1].strip()
            width, height = dims.split('x')
            width = int(width.strip())
            height = int(height.strip())
            
            artworks_data.append((artwork_text, width, height))
        except (ValueError, IndexError) as e:
            print(f"  Warning: Could not parse dimensions: {dimensions_text}", file=sys.stderr)
            continue
    
    return artworks_data


def update_dimensions(db_path="ascii_art.db"):
    """Main function to scrape and update dimensions."""
    print("Updating database with dimensions...\n")
    
    conn = add_dimension_columns(db_path)
    cursor = conn.cursor()
    
    # Fetch all categories
    categories = fetch_category_links()
    
    total_updated = 0
    total_not_found = 0
    
    for idx, (category_name, category_url) in enumerate(categories.items(), 1):
        print(f"\n[{idx}/{len(categories)}] Processing: {category_name}")
        
        # Fetch artworks with dimensions from website
        artworks_data = fetch_artworks_with_dimensions(category_url)
        print(f"  Found {len(artworks_data)} artworks with dimensions")
        
        # Update database
        for artwork_text, width, height in artworks_data:
            # Try to find matching artwork in database
            cursor.execute(
                "SELECT id FROM artworks WHERE artwork = ? LIMIT 1",
                (artwork_text,)
            )
            result = cursor.fetchone()
            
            if result:
                artwork_id = result[0]
                cursor.execute(
                    "UPDATE artworks SET width = ?, height = ? WHERE id = ?",
                    (width, height, artwork_id)
                )
                total_updated += 1
                if total_updated % 9:
                    print(f"{height} x {width}")
            else:
                total_not_found += 1
        
        conn.commit()
        
        # Be nice to the server
        time.sleep(0.5)
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"Dimension update complete!")
    print(f"Updated artworks: {total_updated}")
    print(f"Not found in DB: {total_not_found}")
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        update_dimensions()
    except KeyboardInterrupt:
        print("\n\nUpdate interrupted by user.")
        sys.exit(1)

