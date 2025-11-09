#!/usr/bin/env python3
"""
Random ASCII Art Fetcher
Fetches a random ASCII art piece from asciiart.website and displays it.
"""

import requests
from bs4 import BeautifulSoup
import random
import sys
import argparse
import time


# Headers to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def fetch_category_links(base_url="https://asciiart.website/browse.php"):
    """Fetch all category links and names from the browse page.
    
    Returns:
        dict: Dictionary mapping category names to their URLs
    """
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching browse page: {e}", file=sys.stderr)
        sys.exit(1)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all links to category pages (cat.php?category_id=X)
    categories = {}
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'cat.php?category_id=' in href:
            # Convert relative URL to absolute if needed
            if not href.startswith('http'):
                href = f"https://asciiart.website/{href}"
            
            # Get the category name from the link text
            category_name = link.get_text(strip=True)
            # Remove the count in parentheses if present
            if '(' in category_name:
                category_name = category_name.split('(')[0].strip()
            
            categories[category_name] = href
    
    return categories


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


def list_categories(categories):
    """Print all available categories."""
    print("\nAvailable categories:\n")
    sorted_categories = sorted(categories.keys())
    for category in sorted_categories:
        print(f"  - {category}")
    print(f"\nTotal: {len(categories)} categories")


def find_category(categories, search_term):
    """Find a category by name (case-insensitive partial match).
    
    Args:
        categories: Dictionary of category names to URLs
        search_term: String to search for in category names
        
    Returns:
        tuple: (category_name, category_url) if found, (None, None) otherwise
    """
    search_lower = search_term.lower()
    
    # Try exact match first (case-insensitive)
    for name, url in categories.items():
        if name.lower() == search_lower:
            return name, url
    
    # Try partial match
    matches = [(name, url) for name, url in categories.items() 
               if search_lower in name.lower()]
    
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"\nMultiple categories match '{search_term}':", file=sys.stderr)
        for name, _ in matches:
            print(f"  - {name}", file=sys.stderr)
        print("\nPlease be more specific.", file=sys.stderr)
        return None, None
    else:
        return None, None


def main():
    """Main function to fetch and display random ASCII art."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Fetch random ASCII art from asciiart.website',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Create mutually exclusive group for list-categories
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--list-categories', '-l',
        action='store_true',
        help='List all available categories and exit'
    )
    
    # Category filter (not mutually exclusive with loop)
    parser.add_argument(
        '--category', '-c',
        type=str,
        metavar='NAME',
        help='Filter by category name (case-insensitive, partial match)'
    )
    
    # Loop flag (not mutually exclusive with category)
    parser.add_argument(
        '--loop',
        action='store_true',
        help='Keep displaying random ASCII art (Ctrl+C to exit)'
    )
    
    args = parser.parse_args()
    
    # Get all categories
    categories = fetch_category_links()
    
    if not categories:
        print("No categories found!", file=sys.stderr)
        sys.exit(1)
    
    # Handle --list-categories flag
    if args.list_categories:
        list_categories(categories)
        sys.exit(0)
    
    # Determine if we're filtering by category
    category_filter = None
    if args.category:
        category_name, category_url = find_category(categories, args.category)
        if not category_url:
            print(f"\nCouldn't find category '{args.category}', use --list-categories to see all available categories.\n")
            # Pick a random category instead
            category_name = random.choice(list(categories.keys()))
            category_url = categories[category_name]
        category_filter = (category_name, category_url)
    
    # Main loop for displaying art
    try:
        iteration = 0
        while True:
            # Select category
            if category_filter:
                category_name, category_url = category_filter
                if iteration == 0 and args.loop:
                    print(f"Looping with category: {category_name} (Ctrl+C to exit)\n")
                elif iteration == 0:
                    print(f"Selected category: {category_name}")
            else:
                # Pick a random category
                category_name = random.choice(list(categories.keys()))
                category_url = categories[category_name]
            
            # Fetch artworks from the selected category
            artworks = fetch_artworks_from_category(category_url)
            
            if not artworks:
                if not args.loop:
                    print("No artworks found in this category!", file=sys.stderr)
                    sys.exit(1)
                else:
                    print(f"No artworks found in {category_name}, trying another...\n")
                    iteration += 1
                    continue
            
            # Pick a random artwork
            random_artwork = random.choice(artworks)
            
            # Display the artwork
            print("\n" + "="*60)
            print("RANDOM ASCII ART from https://asciiart.website/browse.php  :")
            print("="*60 + "\n")
            print(random_artwork)
            print("\n" + "="*60)
            
            # If not looping, exit after one
            if not args.loop:
                break
            
            # Small delay before next iteration
            iteration += 1
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nIf you keep his running it hides your traffic from the NSA")
        sys.exit(0)


if __name__ == "__main__":
    main()

