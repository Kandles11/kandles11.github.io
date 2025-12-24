import os
import re
import shutil
import sys
from datetime import datetime

# --- CONFIGURATION ---
INPUT_DIR = 'content'
OUTPUT_DIR = 'docs'
TEMPLATE_DIR = 'templates'
SITE_NAME = "Mason Thomas"

# --- DEPENDENCY CHECK ---
try:
    import markdown
except ImportError:
    print("Error: The 'markdown' library is not installed.")
    print("Please run: pip install markdown")
    sys.exit(1)

class StaticSiteGenerator:
    def __init__(self):
        self.pages = []
        
        # Define your Custom Tags here
        # Syntax in Markdown: [[tag_name::content]]
        self.custom_tags = {
            'alert': '<div class="alert" style="background: #fff3cd; padding: 10px; border: 1px solid #ffeeba; border-radius: 5px; color: #856404;">⚠️ {content}</div>',
            'button': '<button style="background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">{content}</button>',
            'note': '<div class="note" style="border-left: 4px solid #007bff; padding-left: 10px; margin: 10px 0; color: #555;">ℹ️ {content}</div>'
        }

    def ensure_directories(self):
        """Creates the directory structure if it doesn't exist."""
        if not os.path.exists(INPUT_DIR):
            os.makedirs(INPUT_DIR)
            self.create_sample_content()
            
        if not os.path.exists(TEMPLATE_DIR):
            os.makedirs(TEMPLATE_DIR)
            self.create_sample_template()

        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)



    def parse_frontmatter(self, content):
        """
        Separates YAML-style frontmatter from markdown content.
        Returns (metadata_dict, markdown_content)
        """
        metadata = {}
        markdown_content = content

        # Regex to find content between ---
        match = re.match(r'^\s*---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        
        if match:
            frontmatter_str = match.group(1)
            markdown_content = match.group(2)
            
            # Simple line-by-line parser (avoids needing PyYAML dependency)
            for line in frontmatter_str.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip().strip('"').strip("'")
        
        return metadata, markdown_content

    def process_custom_tags(self, content):
        """
        Finds [[tag::content]] patterns and replaces them with HTML.
        """
        def replace_tag(match):
            tag_name = match.group(1)
            tag_content = match.group(2)
            
            if tag_name in self.custom_tags:
                return self.custom_tags[tag_name].format(content=tag_content)
            return match.group(0) # Return original if tag not defined

        # Regex: [[ capture_name :: capture_content ]]
        pattern = r'\[\[(\w+)::(.*?)\]\]'
        return re.sub(pattern, replace_tag, content)

    def process_article(self, md_path, output_path, template):
        """Process a single markdown file and generate HTML."""
        print(f"Processing {md_path}...")
        
        with open(md_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        # 1. Parse Metadata
        metadata, md_body = self.parse_frontmatter(raw_content)
        
        # 2. Process Custom Tags (before Markdown conversion)
        processed_md = self.process_custom_tags(md_body)
        
        # 3. Convert Markdown to HTML
        html_content = markdown.markdown(processed_md)
        
        # 4. Prepare injection variables
        title = metadata.get('title') or self.extract_title_from_markdown(md_body)
        date_str = metadata.get('date') or metadata.get('created')
        formatted_date = ''
        
        # Format date for display
        if date_str:
            try:
                # Try various date formats
                formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y', '%B %d, %Y', '%b %d, %Y']
                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_str.strip(), fmt)
                        # Format as "Month DD, YYYY" (e.g., "December 23, 2025")
                        formatted_date = dt.strftime('%B %d, %Y')
                        break
                    except ValueError:
                        continue
            except:
                pass
        
        custom_css = metadata.get('custom_css', '')
        custom_html = metadata.get('custom_html', '')
        
        # 5. Render Template
        # We use simple string replacement to avoid Jinja2 dependency for simplicity
        final_html = template.replace('{{ title }}', title)
        final_html = final_html.replace('{{ date }}', formatted_date)
        final_html = final_html.replace('{{ site_name }}', SITE_NAME)
        final_html = final_html.replace('{{ content }}', html_content)
        final_html = final_html.replace('{{ custom_css }}', custom_css)
        final_html = final_html.replace('{{ custom_html }}', custom_html)
        final_html = final_html.replace('{{ build_date }}', datetime.now().strftime("%Y-%m-%d %H:%M"))

        # 6. Write to Output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)

    def copy_article_assets(self, source_dir, dest_dir):
        """Copy all non-markdown files from source to destination."""
        if not os.path.exists(source_dir):
            return
        
        os.makedirs(dest_dir, exist_ok=True)
        
        for item in os.listdir(source_dir):
            source_path = os.path.join(source_dir, item)
            dest_path = os.path.join(dest_dir, item)
            
            # Skip markdown files and hidden files
            if item.endswith('.md') or item.startswith('.'):
                continue
            
            if os.path.isdir(source_path):
                # Recursively copy directories
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            else:
                # Copy files
                shutil.copy2(source_path, dest_path)

    def extract_title_from_markdown(self, content):
        """Extract title from first heading if no frontmatter title."""
        # Look for first # heading
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return 'Untitled'

    def parse_date(self, date_str):
        """Parse date string and return (year, formatted_date)."""
        if not date_str:
            return None, None
        
        try:
            # Try various date formats
            formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y', '%B %d, %Y', '%b %d, %Y']
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    year = dt.year
                    # Format as "Mon DD" (e.g., "Oct 30")
                    formatted = dt.strftime('%b %d')
                    return year, formatted
                except ValueError:
                    continue
        except:
            pass
        
        return None, None

    def collect_articles(self):
        """Collect all articles and their metadata."""
        articles = []
        items = os.listdir(INPUT_DIR)
        
        for item in items:
            item_path = os.path.join(INPUT_DIR, item)
            
            # Skip index.md and about.md
            if item in ['index.md', 'about.md']:
                continue
            
            # Check if it's a directory (folder-based article)
            if os.path.isdir(item_path):
                md_filename = f"{item}.md"
                md_path = os.path.join(item_path, md_filename)
                
                if os.path.exists(md_path):
                    with open(md_path, 'r', encoding='utf-8') as f:
                        raw_content = f.read()
                    
                    metadata, _ = self.parse_frontmatter(raw_content)
                    title = metadata.get('title') or self.extract_title_from_markdown(raw_content)
                    date_str = metadata.get('date') or metadata.get('created')
                    
                    # Use file modification time as fallback
                    if not date_str:
                        mtime = os.path.getmtime(md_path)
                        dt = datetime.fromtimestamp(mtime)
                        date_str = dt.strftime('%Y-%m-%d')
                    
                    year, formatted_date = self.parse_date(date_str)
                    if not year:
                        year = datetime.now().year
                        formatted_date = datetime.now().strftime('%b %d')
                    
                    # Calculate sort_date for proper sorting
                    try:
                        if date_str and '-' in date_str:
                            sort_date = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
                        else:
                            sort_date = datetime(year, 1, 1)
                    except:
                        sort_date = datetime(year, 1, 1)
                    
                    # URL is the folder name
                    url = f"/{item}/"
                    articles.append({
                        'title': title,
                        'url': url,
                        'date': formatted_date,
                        'year': year,
                        'sort_date': sort_date
                    })
            
            # Check if it's a standalone markdown file (excluding index and about)
            elif item.endswith('.md'):
                with open(item_path, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
                
                metadata, _ = self.parse_frontmatter(raw_content)
                title = metadata.get('title') or self.extract_title_from_markdown(raw_content)
                date_str = metadata.get('date') or metadata.get('created')
                
                # Use file modification time as fallback
                if not date_str:
                    mtime = os.path.getmtime(item_path)
                    dt = datetime.fromtimestamp(mtime)
                    date_str = dt.strftime('%Y-%m-%d')
                
                year, formatted_date = self.parse_date(date_str)
                if not year:
                    year = datetime.now().year
                    formatted_date = datetime.now().strftime('%b %d')
                
                # Calculate sort_date for proper sorting
                try:
                    if date_str and '-' in date_str:
                        sort_date = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
                    else:
                        sort_date = datetime(year, 1, 1)
                except:
                    sort_date = datetime(year, 1, 1)
                
                # URL is the HTML filename
                url = f"/{item.replace('.md', '.html')}"
                articles.append({
                    'title': title,
                    'url': url,
                    'date': formatted_date,
                    'year': year,
                    'sort_date': sort_date
                })
        
        # Sort articles by date (newest first)
        articles.sort(key=lambda x: x['sort_date'], reverse=True)
        return articles

    def generate_article_list_html(self, articles):
        """Generate HTML for article list grouped by year."""
        if not articles:
            return '<div class="year-group"><div class="year-container"><p class="year">No articles yet</p></div></div>'
        
        # Group articles by year
        articles_by_year = {}
        for article in articles:
            year = article['year']
            if year not in articles_by_year:
                articles_by_year[year] = []
            articles_by_year[year].append(article)
        
        # Sort years descending
        years = sorted(articles_by_year.keys(), reverse=True)
        
        html_parts = []
        for year in years:
            year_articles = articles_by_year[year]
            html_parts.append(f'<div class="year-group">')
            html_parts.append(f'  <div class="year-container"><p class="year">{year}</p></div>')
            
            for article in year_articles:
                html_parts.append(f'  <div class="post">')
                html_parts.append(f'    <span class="date">{article["date"]}</span>')
                html_parts.append(f'    <a href="{article["url"]}">{article["title"]}</a>')
                html_parts.append(f'  </div>')
            
            html_parts.append(f'</div>')
        
        return '\n'.join(html_parts)

    def build(self):
        print("Starting build process...")
        self.ensure_directories()
        
        # Load Templates
        base_template_path = os.path.join(TEMPLATE_DIR, 'base.html')
        home_template_path = os.path.join(TEMPLATE_DIR, 'home.html')
        article_template_path = os.path.join(TEMPLATE_DIR, 'article.html')
        
        with open(base_template_path, 'r', encoding='utf-8') as f:
            base_template = f.read()
        
        # Load home template if it exists
        home_template = None
        if os.path.exists(home_template_path):
            with open(home_template_path, 'r', encoding='utf-8') as f:
                home_template = f.read()
        
        # Load article template if it exists
        article_template = None
        if os.path.exists(article_template_path):
            with open(article_template_path, 'r', encoding='utf-8') as f:
                article_template = f.read()
        else:
            # Fallback to base template if article template doesn't exist
            article_template = base_template
        
        # Collect all articles for the home page
        articles = self.collect_articles()
        article_list_html = self.generate_article_list_html(articles)

        # Generate homepage from home.html template (no index.md needed)
        if home_template:
            index_path = os.path.join(OUTPUT_DIR, 'index.html')
            final_html = home_template.replace('{{ article_list }}', article_list_html)
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(final_html)
            print("Generating homepage from home.html template...")

        # Process all items in content directory
        items = os.listdir(INPUT_DIR)
        
        for item in items:
            item_path = os.path.join(INPUT_DIR, item)
            
            # Skip index.md since homepage is generated from template
            if item == 'index.md':
                continue
            
            # Check if it's a directory (folder-based article)
            if os.path.isdir(item_path):
                # Look for markdown file matching folder name
                md_filename = f"{item}.md"
                md_path = os.path.join(item_path, md_filename)
                
                if os.path.exists(md_path):
                    # Create output directory for this article
                    output_dir = os.path.join(OUTPUT_DIR, item)
                    output_path = os.path.join(output_dir, 'index.html')
                    
                    # Process the markdown file with article template
                    self.process_article(md_path, output_path, article_template)
                    
                    # Copy all assets (images, etc.) to output directory
                    self.copy_article_assets(item_path, output_dir)
                else:
                    print(f"Warning: No {md_filename} found in {item}/ directory, skipping...")
            
            # Check if it's a standalone markdown file
            elif item.endswith('.md'):
                md_path = item_path
                output_filename = item.replace('.md', '.html')
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                
                # Use article template for articles, base template for about.md and others
                if item != 'about.md' and article_template:
                    # Use article template for articles (not about.md)
                    self.process_article(md_path, output_path, article_template)
                else:
                    # Use base template for about.md and other pages
                    self.process_article(md_path, output_path, base_template)

        print(f"Build complete! Files generated in '{OUTPUT_DIR}/'")

if __name__ == "__main__":
    generator = StaticSiteGenerator()
    generator.build()