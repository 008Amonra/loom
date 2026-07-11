#!/usr/bin/env python3
"""
Blog builder for 45dgof8.com/blog
Converts markdown posts to static HTML pages.

Usage:
    python3 build.py              # Build all posts
    python3 build.py --watch      # Watch for changes and rebuild
    python3 build.py post.md      # Build single post
"""

import os
import sys
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path

import markdown

BLOG_DIR = Path(__file__).parent
POSTS_DIR = BLOG_DIR / "posts"
TEMPLATE = BLOG_DIR / "template.html"
INDEX_TEMPLATE = BLOG_DIR / "index-template.html"
OUTPUT_DIR = BLOG_DIR  # HTML files go directly in /blog/
ANALYTICS_ID = None  # Set to Cloudflare Web Analytics tag if available

# Cloudflare Web Analytics - add your tag here when you get it
# Get it from: https://dash.cloudflare.com → Analytics → Web Analytics
CF_ANALYTICS_TAG = None  # e.g., "your-tag-id.js"


def parse_frontmatter(content):
    """Extract YAML-like frontmatter from markdown."""
    meta = {}
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            fm = content[3:end].strip()
            for line in fm.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip().strip('"').strip("'")
            content = content[end + 3:].strip()
    return meta, content


def slug_from_filename(filename):
    """Convert filename to URL slug."""
    name = Path(filename).stem
    # Remove date prefix if present (e.g., 2026-07-11-my-post → my-post)
    name = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name)
    return name


def render_post(meta, html_content, slug):
    """Render a blog post using the template."""
    title = meta.get("title", slug.replace("-", " ").title())
    description = meta.get("description", "")
    date = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
    author = meta.get("author", "Jens")
    image = meta.get("image", "")
    tags = meta.get("tags", "")

    # Hero image HTML
    hero_html = ""
    if image:
        hero_html = f'<img src="{image}" alt="{title}" class="hero-img" loading="eager">'

    # Format date nicely
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        date_display = dt.strftime("%B %d, %Y")
    except ValueError:
        date_display = date

    # Build meta tags
    meta_tags = f"""<meta name="description" content="{description}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://008amonra.github.io/loom/blog/{slug}/">
<meta property="article:published_time" content="{date}">
<meta property="article:author" content="{author}">"""
    if image:
        meta_tags += f'\n<meta property="og:image" content="{image}">'

    # Analytics snippet
    analytics = ""
    if CF_ANALYTICS_TAG:
        analytics = f'<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{{"token": "{CF_ANALYTICS_TAG}"}}\'></script>'

    template = TEMPLATE.read_text()
    html = template.replace("{{TITLE}}", title)
    html = html.replace("{{DESCRIPTION}}", description)
    html = html.replace("{{META_TAGS}}", meta_tags)
    html = html.replace("{{DATE_DISPLAY}}", date_display)
    html = html.replace("{{AUTHOR}}", author)
    html = html.replace("{{HERO_IMAGE}}", hero_html)
    html = html.replace("{{CONTENT}}", html_content)
    html = html.replace("{{SLUG}}", slug)
    html = html.replace("{{ANALYTICS}}", analytics)
    return html


def render_index(posts):
    """Render the blog index page."""
    posts_html = ""
    for post in sorted(posts, key=lambda p: p["date"], reverse=True):
        hero_img = post.get("image", "")
        hero_html = f'<img src="{hero_img}" alt="{post["title"]}" class="hero-thumb" loading="lazy">' if hero_img else ""
        posts_html += f"""
        <article class="post-card">
            {hero_html}
            <time>{post["date_display"]}</time>
            <h2><a href="/blog/{post["slug"]}/">{post["title"]}</a></h2>
            <p>{post["description"]}</p>
            <div class="post-tags">{post["tags_html"]}</div>
        </article>"""

    template = INDEX_TEMPLATE.read_text()
    html = template.replace("{{POSTS}}", posts_html)

    analytics = ""
    if CF_ANALYTICS_TAG:
        analytics = f'<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{{"token": "{CF_ANALYTICS_TAG}"}}\'></script>'
    html = html.replace("{{ANALYTICS}}", analytics)

    return html


def build_post(md_path):
    """Build a single post from markdown."""
    content = md_path.read_text(encoding="utf-8")
    meta, md_content = parse_frontmatter(content)

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=["extra", "codehilite", "toc", "attr_list"])
    html_content = md.convert(md_content)

    slug = slug_from_filename(md_path.name)
    html = render_post(meta, html_content, slug)

    # Write output
    out_dir = OUTPUT_DIR / slug
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(html, encoding="utf-8")
    print(f"  ✓ {slug}/index.html")

    # Return metadata for index
    date = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        date_display = dt.strftime("%B %d, %Y")
    except ValueError:
        date_display = date

    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    tags_html = " ".join(f'<span class="tag">{t}</span>' for t in tags)

    return {
        "title": meta.get("title", slug.replace("-", " ").title()),
        "description": meta.get("description", ""),
        "date": date,
        "date_display": date_display,
        "slug": slug,
        "tags": tags,
        "tags_html": tags_html,
        "image": meta.get("image", ""),
    }


def main():
    print("🔨 Building blog...")

    # Find all markdown files in posts/
    md_files = sorted(POSTS_DIR.glob("*.md"))
    if not md_files:
        print("  No posts found in posts/")
        return

    posts = []
    for md_path in md_files:
        if md_path.name.startswith("_"):
            continue  # Skip draft files
        print(f"  Processing: {md_path.name}")
        post_meta = build_post(md_path)
        posts.append(post_meta)

    # Build index
    index_html = render_index(posts)
    index_file = OUTPUT_DIR / "index.html"
    index_file.write_text(index_html, encoding="utf-8")
    print(f"  ✓ index.html ({len(posts)} posts)")

    print(f"\n✅ Blog built: {len(posts)} posts in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
