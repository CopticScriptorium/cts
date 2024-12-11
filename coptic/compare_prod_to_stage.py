import aiohttp
import asyncio
import difflib
import re

# List of URLs to compare
URLS = [
    "/index/places/",
    "/index/people/",
    "/index/msName/",
    "/index/author/",
    "/index/corpus/",
    "/texts/magicalpapyri/",
    "/texts/magicalpapyri/curse-to-bring-suffering-pain-and-disease/norm/",
    "/texts/magicalpapyri/curse-to-bring-suffering-pain-and-disease/analytic/",
    "/texts/magicalpapyri/curse-to-bring-suffering-pain-and-disease/dipl/",
    "/texts/victor/martyrdom-of-victor-part-6/analytic",
    "/search?text=besa",
    "/search?text=besa&author=Besa&corpus=besa.letters&msName=CM.1643",
    "/search?text=amir&author=Mena+of+Pshati",
]

PROD_URL = "https://data.copticscriptorium.org"
STAGE_URL = "http://localhost:8000"


async def fetch_content(session, url):
    """Fetch raw HTML content from a URL and normalize it."""
    try:
        async with session.get(url) as response:
            html = await response.text()
            return normalize_text(html)
    except Exception as e:
        return f"Error fetching {url}: {e}"


async def fetch_urls_concurrently(base_url, urls):
    """Fetch multiple URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_content(session, f"{base_url}{url}") for url in urls]
        return await asyncio.gather(*tasks)


def compare_content(content1, content2):
    """Compare two pieces of HTML content and highlight differences."""
    diff = difflib.unified_diff(
        content1.splitlines(), content2.splitlines(), lineterm="", 
        fromfile="PROD", tofile="STAGE"
    )
    return "\n".join(diff)

def normalize_text(html):
    """
    Normalize the HTML content by:
    1. Replacing multiple spaces with a single space.
    2. Replacing multiple newlines with a single newline.
    3. Removing newlines after attributes' closing double quotes.
    4. Adding a newline after specified opening and closing tags.
    """
    # Step 1: Replace multiple spaces with a single space
    html = re.sub(r" {2,}", " ", html)
    
    # Step 2: Replace multiple newlines with a single newline
    html = re.sub(r"\n{2,}", "\n", html)
    
    # Step 3: Remove newlines immediately following attributes' closing double quotes
    html = re.sub(r'"\s*\n\s*', '" ', html)
    
    # Step 4: Add a newline after specified tags
    tags = ["head", "title", "body", "div", "link", "meta", "nav", "header", "script", "ul", "li", "p"]
    tag_pattern = "|".join(tags)
    html = re.sub(rf"(</?({tag_pattern})[^>]*>)", r"\1\n", html, flags=re.IGNORECASE)
    
    # Remove any redundant newlines introduced by Step 4
    html = re.sub(r"\n{2,}", "\n", html)
    
    return html.strip()


async def main():
    # Fetch HTML content from both websites
    prod_content, stage_content = await asyncio.gather(
        fetch_urls_concurrently(PROD_URL, URLS),
        fetch_urls_concurrently(STAGE_URL, URLS),
    )
    
    # Compare HTML content
    for idx, url in enumerate(URLS):
        print(f"Comparing {url}...")
        diff = compare_content(prod_content[idx], stage_content[idx])
        if diff:
            print(diff)
        else:
            print("No differences found.")

# Run the main event loop
if __name__ == "__main__":
    asyncio.run(main())