import os
from datetime import datetime
from bs4 import BeautifulSoup

# === Configuration ===
ARTICLES_DIR = 'articles'
TEMPLATES_DIR = 'templates'
OUTPUT_DIR = 'docs'
HEADER_FILE = os.path.join(TEMPLATES_DIR, 'header.html')

# === Helpers ===

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_metadata_from_html(content):
    """Extract metadata from <meta name="..." content="..."> tags."""
    soup = BeautifulSoup(content, 'html.parser')
    metadata = {}

    for meta_tag in soup.find_all('meta'):
        name = meta_tag.get('name')
        value = meta_tag.get('content')
        if name and value:
            metadata[name.strip()] = value.strip()

    return metadata

def safe_parse_date(date_str):
    """Try to parse a date string into a datetime object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None

# === Main Generation Logic ===

def main():
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read templates
    header = read_file(HEADER_FILE)

    # Scan articles
    articles = []

    for filename in os.listdir(ARTICLES_DIR):
        if filename.endswith('.html'):
            path = os.path.join(ARTICLES_DIR, filename)
            content = read_file(path)

            # Extract metadata
            metadata = extract_metadata_from_html(content)
            title = metadata.get('title', filename)
            created = metadata.get('created', 'unknown')
            updated = metadata.get('updated', 'unknown')

            slug = os.path.splitext(filename)[0]

            articles.append({
                'filename': filename,
                'slug': slug,
                'title': title,
                'created': created,
                'updated': updated,
                'content': content,
            })

    # Sort articles by updated date, newest first
    articles.sort(key=lambda a: safe_parse_date(a['updated']) or datetime.min, reverse=True)

    # Generate wrapped articles in subfolders
    for article in articles:
        wrapped_content = header + '\n' + article['content'] + '\n'
        article_dir = os.path.join(OUTPUT_DIR, article['slug'])
        output_path = os.path.join(article_dir, 'index.html')
        write_file(output_path, wrapped_content)

    # Generate homepage
    homepage = header
    homepage += '<h1>All Articles</h1>\n<ul>\n'

    for article in articles:
        homepage += f'  <li><span>{article["updated"]} : </span><a href="{article["slug"]}/">{article["title"]}</a></li>\n'

    homepage += '</ul>\n'

    write_file(os.path.join(OUTPUT_DIR, 'index.html'), homepage)
    
    write_file(os.path.join(OUTPUT_DIR, 'styles/index.css'), read_file(os.path.join(TEMPLATES_DIR, 'styles/index.css')))
    write_file(os.path.join(OUTPUT_DIR, 'styles/article.css'), read_file(os.path.join(TEMPLATES_DIR, 'styles/article.css')))

    print(f"✅ Site generated in '{OUTPUT_DIR}/'")

if __name__ == "__main__":
    main()
