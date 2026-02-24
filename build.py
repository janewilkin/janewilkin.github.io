#!/usr/bin/env python3
"""Build article HTML from markdown sources.

Reads content/*.md files with YAML frontmatter, renders markdown to HTML,
applies the Jinja2 article template, and writes to blog/{slug}.html.

Usage:
    python build.py                    # Build all articles
    python build.py the-bottleneck-moved  # Build a single article
"""

import re
import sys
from pathlib import Path

import frontmatter
from jinja2 import Environment, FileSystemLoader
from markdown_it import MarkdownIt

SITE_DIR = Path(__file__).parent
CONTENT_DIR = SITE_DIR / "content"
TEMPLATE_DIR = SITE_DIR / "templates"
OUTPUT_DIR = SITE_DIR / "blog"

INDENT = "          "

# Block-level elements that should have blank lines between them
BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ol", "ul", "pre", "blockquote"}


def _add_external_link_attrs(html: str) -> str:
    """Add target='_blank' rel='noopener' to external links."""

    def replace_link(match: re.Match) -> str:
        href = match.group(1)
        if href.startswith(("http://", "https://")):
            return f'<a href="{href}" target="_blank" rel="noopener">'
        return match.group(0)

    return re.sub(r'<a href="([^"]*)">', replace_link, html)


def _indent_html(html: str) -> str:
    """Indent rendered HTML to match article-body nesting depth.

    Block elements get indented. Content inside <pre> blocks is NOT indented
    because whitespace is significant there. Blank lines are inserted between
    block-level elements for readability.
    """
    lines = html.splitlines()
    result = []
    in_pre = False
    prev_was_block_close = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Track <pre> state
        if stripped.startswith("<pre"):
            # Insert blank line before <pre> if previous was a block close
            if prev_was_block_close:
                result.append("")
            result.append("")
            # Don't indent <pre> blocks at all - put them at column 0
            result.append(line)
            in_pre = True
            prev_was_block_close = False
            if "</pre>" in stripped:
                in_pre = False
                prev_was_block_close = True
            continue

        if in_pre:
            result.append(line)
            if "</pre>" in stripped:
                in_pre = False
                prev_was_block_close = True
            continue

        # Check if this line starts a new block element
        is_block_open = False
        for tag in BLOCK_TAGS:
            if stripped.startswith(f"<{tag}") or stripped.startswith(f"</{tag}"):
                is_block_open = True
                break

        # Add blank line between block elements
        if is_block_open and prev_was_block_close:
            result.append("")

        result.append(INDENT + stripped)

        # Track if this line closes a block element
        prev_was_block_close = False
        for tag in BLOCK_TAGS:
            if f"</{tag}>" in stripped:
                prev_was_block_close = True
                break

    return "\n".join(result).strip("\n")


def render_markdown(text: str) -> str:
    """Render markdown to HTML with proper formatting for article pages."""
    md = MarkdownIt("default", {"html": True, "typographer": True})
    raw_html = md.render(text)

    html = _add_external_link_attrs(raw_html)
    html = _indent_html(html)

    return html


def build_article(slug: str, env: Environment) -> Path:
    """Build a single article from markdown to HTML."""
    md_path = CONTENT_DIR / f"{slug}.md"
    if not md_path.exists():
        print(f"  ERROR: {md_path} not found", file=sys.stderr)
        sys.exit(1)

    post = frontmatter.load(md_path)

    content_html = render_markdown(post.content)

    template = env.get_template("article.html")
    html = template.render(
        title=post["title"],
        date=post["date"],
        reading_time=post["reading_time"],
        description=post["description"],
        content=content_html,
    )

    output_path = OUTPUT_DIR / f"{slug}.html"
    output_path.write_text(html + "\n")
    return output_path


def main() -> None:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=False,
        keep_trailing_newline=True,
    )

    if len(sys.argv) > 1:
        slugs = sys.argv[1:]
    else:
        slugs = sorted(p.stem for p in CONTENT_DIR.glob("*.md"))

    if not slugs:
        print("No content files found in content/")
        sys.exit(1)

    print(f"Building {len(slugs)} article(s)...")
    for slug in slugs:
        output = build_article(slug, env)
        print(f"  {output.relative_to(SITE_DIR)}")

    print("Done.")


if __name__ == "__main__":
    main()
