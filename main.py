from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
import time

INDEX_URL = "https://www.atlasofwonders.com/p/movies-filming-locations.html"


# -----------------------------------
# GET MOVIE LINKS
# -----------------------------------
def get_movie_links(page):

    print("Opening movie database page...")

    page.goto(
        INDEX_URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    page.wait_for_timeout(5000)

    # Scroll to load more movies
    for _ in range(10):
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(1200)

    html = page.content()

    soup = BeautifulSoup(html, "html.parser")

    movie_links = []

    # Find all image links
    links = soup.find_all("a")

    for link in links:

        href = link.get("href")

        img = link.find("img")

        if not href or not img:
            continue

        alt = img.get("alt")

        if not alt:
            continue

        # Clean movie title
        title = (
            alt.replace("Where was ", "")
               .replace(" filmed", "")
               .strip()
        )

        # Only actual movie articles
        if "atlasofwonders.com/20" not in href:
            continue

        movie_links.append({
            "title": title,
            "url": href
        })

    # Remove duplicates
    unique = {}

    for movie in movie_links:
        unique[movie["url"]] = movie

    cleaned = list(unique.values())

    print(f"\nFound {len(cleaned)} movies\n")

    for movie in cleaned[:20]:
        print(movie)

    return cleaned

# -----------------------------------
# EXTRACT LOCATIONS
# -----------------------------------
def extract_locations(text):

    patterns = [

        r"filmed in ([A-Z][a-zA-Z\\s,]+)",
        r"shot in ([A-Z][a-zA-Z\\s,]+)",
        r"located in ([A-Z][a-zA-Z\\s,]+)",
        r"in ([A-Z][a-zA-Z\\s]+, [A-Z][a-zA-Z\\s]+)",
        r"([A-Z][a-zA-Z\\s]+, England)",
        r"([A-Z][a-zA-Z\\s]+, Scotland)",
        r"([A-Z][a-zA-Z\\s]+, Wales)",
        r"([A-Z][a-zA-Z\\s]+, Ireland)",
    ]

    locations = []

    for pattern in patterns:

        matches = re.findall(pattern, text)

        for match in matches:

            cleaned = (
                match.strip()
                .split(".")[0]
                .split("\\n")[0]
            )

            if len(cleaned) > 3:
                locations.append(cleaned)

    # Remove duplicates
    locations = list(set(locations))

    return locations[:15]

# -----------------------------------
# PARSE MOVIE PAGE
# -----------------------------------
def parse_movie_page(page, movie):

    try:

        print(f"Parsing: {movie['title']}")

        page.goto(
            movie["url"],
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(7000)

        # Scroll deeply
        for _ in range(6):
            page.mouse.wheel(0, 4000)
            page.wait_for_timeout(1200)

        # Extract ALL visible text elements
        elements = page.locator("div, p, span, b")

        texts = []

        count = elements.count()

        for i in range(count):

            try:

                text = elements.nth(i).inner_text().strip()

                # Ignore junk
                if len(text) < 25:
                    continue

                lower = text.lower()

                junk_words = [
                    "privacy policy",
                    "advertisement",
                    "cookie",
                    "all rights reserved",
                    "follow us",
                    "google_ads",
                    "themexpose"
                ]

                if any(word in lower for word in junk_words):
                    continue

                texts.append(text)

            except:
                pass

        combined_text = " ".join(texts)

        print("\nARTICLE SAMPLE:\n")
        print(combined_text[:3000])

        locations = extract_locations(combined_text)

        print("\nLOCATIONS FOUND:")
        print(locations)

        return {
            "title": movie["title"],
            "locations": locations
        }

    except Exception as e:

        print(f"FAILED: {movie['title']}")
        print(e)

        return None


# -----------------------------------
# MAIN
# -----------------------------------
def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
        headless=False,
        channel="chrome"
        )

        page = browser.new_page()

        movie_links = get_movie_links(page)

        results = {}

        # TEST SMALL FIRST
        for movie in movie_links:

            parsed = parse_movie_page(page, movie)

            if parsed and parsed["locations"]:

                results[parsed["title"]] = parsed["locations"]

                # SAVE AFTER EACH MOVIE
                with open("movie_locations2.json", "w") as f:

                    json.dump(results, f, indent=2)
                
            time.sleep(1)


        print("\\nDONE")
        print("Saved movie_locations2.json")

        browser.close()


if __name__ == "__main__":
    main()