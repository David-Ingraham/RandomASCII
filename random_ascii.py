#!/usr/bin/env python3
"""
Random ASCII Art Fetcher
Fetches a random ASCII art piece from asciiart.website and displays it.
"""

import requests
from bs4 import BeautifulSoup
import random
import sys


# Headers to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def fetch_category_links(base_url="https://asciiart.website/browse.php"):
    """Fetch all category links from the browse page."""
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching browse page: {e}", file=sys.stderr)
        sys.exit(1)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all links to category pages (cat.php?category_id=X)
    category_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'cat.php?category_id=' in href:
            # Convert relative URL to absolute if needed
            if not href.startswith('http'):
                href = f"https://asciiart.website/{href}"
            category_links.append(href)
    
    return category_links


def fetch_artworks_from_category(category_url):
    """Fetch all ASCII artworks from a category page."""
    try:
        response = requests.get(category_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching category page: {e}", file=sys.stderr)
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all pre tags containing ASCII art
    artworks = []
    pre_tags = soup.find_all('pre', class_='adu-artwork-pre')
    
    for pre in pre_tags:
        artwork_text = pre.get_text()
        if artwork_text.strip():  # Only add non-empty artworks
            artworks.append(artwork_text)
    
    return artworks


def main():
    """Main function to fetch and display random ASCII art."""
    
    
    # Get all category links
    category_links = fetch_category_links()
    
    if not category_links:
        print("No categories found!", file=sys.stderr)
        sys.exit(1)
    
    
    
    # Pick a random category
    random_category = random.choice(category_links)
    
    
    # Fetch artworks from that category
    
    artworks = fetch_artworks_from_category(random_category)
    
    if not artworks:
        print("No artworks found in this category!", file=sys.stderr)
        sys.exit(1)
    
    
    
    # Pick a random artwork
    random_artwork = random.choice(artworks)
    
    # Display the artwork
    print("\n" + "="*60)
    print("RANDOM ASCII ART from https://asciiart.website/browse.php  :")
    print("="*60 + "\n")
    print(random_artwork)
    print("\n" + "="*60)


if __name__ == "__main__":
    main()

