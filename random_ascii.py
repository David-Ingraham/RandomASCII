#!/usr/bin/env python3
"""
Random ASCII Art Fetcher (Database Version)
Fetches random ASCII art from local SQLite database.
"""

import sqlite3
import random
import sys
import argparse
import time
import os
from colorama import init as colorama_init


# ANSI color codes
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'reset': '\033[0m'
}


def get_db_connection(db_path="ascii_art.db"):
    """Get a connection to the SQLite database."""
    if not os.path.exists(db_path):
        print(f"Error: Database '{db_path}' not found!", file=sys.stderr)
        print(f"Please run 'python build_db.py' first to create the database.", file=sys.stderr)
        sys.exit(1)
    
    return sqlite3.connect(db_path)


def fetch_categories(conn):
    """Fetch all categories from the database.
    
    Returns:
        dict: Dictionary mapping category names to their IDs
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories ORDER BY name")
    return {name: cat_id for cat_id, name in cursor.fetchall()}


def fetch_artworks_from_category(conn, category_id):
    """Fetch all ASCII artworks from a category.
    
    Args:
        conn: SQLite connection
        category_id: Category ID
        
    Returns:
        list: List of artwork strings
    """
    cursor = conn.cursor()
    cursor.execute("SELECT artwork FROM artworks WHERE category_id = ?", (category_id,))
    return [row[0] for row in cursor.fetchall()]


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
        categories: Dictionary of category names to IDs
        search_term: String to search for in category names
        
    Returns:
        tuple: (category_name, category_id) if found, (None, None) otherwise
    """
    search_lower = search_term.lower()
    
    # Try exact match first (case-insensitive)
    for name, cat_id in categories.items():
        if name.lower() == search_lower:
            return name, cat_id
    
    # Try partial match
    matches = [(name, cat_id) for name, cat_id in categories.items() 
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


def colorize_artwork(artwork, color_names):
    """Apply colors to artwork, splitting evenly if multiple colors.
    
    Args:
        artwork: The ASCII art string to colorize
        color_names: List of color names to apply
        
    Returns:
        str: Colorized artwork string
    """
    if not color_names:
        return artwork
    
    # Validate colors
    valid_colors = [c for c in color_names if c.lower() in COLORS]
    if not valid_colors:
        return artwork
    
    lines = artwork.split('\n')
    total_lines = len(lines)
    lines_per_color = total_lines // len(valid_colors)
    
    colored_lines = []
    for i, line in enumerate(lines):
        color_index = min(i // lines_per_color, len(valid_colors) - 1)
        color_code = COLORS[valid_colors[color_index].lower()]
        colored_lines.append(color_code + line + COLORS['reset'])
    
    return '\n'.join(colored_lines)


def main():
    """Main function to fetch and display random ASCII art."""
    # Initialize colorama for cross-platform color support
    colorama_init()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Fetch random ASCII art from local database',
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
    
    # Color flag
    parser.add_argument(
        '--color',
        type=str,
        nargs='+',
        metavar='COLOR',
        help='Color the output (red, green, yellow, blue, magenta, cyan, white). Multiple colors split the art proportionally.'
    )
    
    # Delay flag
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        metavar='SECONDS',
        help='Delay in seconds between artworks in loop mode (default: 1.0, use 0 for instant)'
    )
    
    args = parser.parse_args()
    
    # Connect to database
    conn = get_db_connection()
    
    # Get all categories
    categories = fetch_categories(conn)
    
    if not categories:
        print("No categories found in database!", file=sys.stderr)
        conn.close()
        sys.exit(1)
    
    # Handle --list-categories flag
    if args.list_categories:
        list_categories(categories)
        conn.close()
        sys.exit(0)
    
    # Determine if we're filtering by category
    category_filter = None
    if args.category:
        category_name, category_id = find_category(categories, args.category)
        if not category_id:
            print(f"\nCouldn't find category '{args.category}', use --list-categories to see all available categories.\n")
            # Pick a random category instead
            category_name = random.choice(list(categories.keys()))
            category_id = categories[category_name]
        category_filter = (category_name, category_id)
    
    # Main loop for displaying art
    try:
        iteration = 0
        while True:
            # Select category
            if category_filter:
                category_name, category_id = category_filter
                if iteration == 0 and args.loop:
                    print(f"Looping with category: {category_name} (Ctrl+C to exit)\n")
                elif iteration == 0:
                    print(f"Selected category: {category_name}")
            else:
                # Pick a random category
                category_name = random.choice(list(categories.keys()))
                category_id = categories[category_name]
            
            # Fetch artworks from the selected category
            artworks = fetch_artworks_from_category(conn, category_id)
            
            if not artworks:
                if not args.loop:
                    print("No artworks found in this category!", file=sys.stderr)
                    conn.close()
                    sys.exit(1)
                else:
                    print(f"No artworks found in {category_name}, trying another...\n")
                    iteration += 1
                    continue
            
            # Pick a random artwork
            random_artwork = random.choice(artworks)
            
            # Display the artwork
            print("\n" + "="*60)
            print(" ASCII ART from https://asciiart.website/browse.php :")
            print("="*60 + "\n")
            
            # Apply color if requested
            if args.color:
                random_artwork = colorize_artwork(random_artwork, args.color)
            
            print(random_artwork)
            print("\n" + "="*60)
            
            # If not looping, exit after one
            if not args.loop:
                break
            
            # Delay before next iteration
            iteration += 1
            if args.delay > 0:
                time.sleep(args.delay)
            
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()
        sys.exit(0)


if __name__ == "__main__":
    main()

