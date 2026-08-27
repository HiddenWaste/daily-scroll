import requests
from bs4 import BeautifulSoup
import time

#################
# CONFIGURATION #
#################

# = {{{

# Array of target programming languages (slugs used in GitHub URLs)
#    Use lowercase names (e.g., 'python', 'javascript', 'c++', 'typescript', 'rust', 'go')
LANGUAGES = ["python", "javascript", "rust", "go", "c++"]
NUM_REPOS = 6 # Number of top trending repos to fetch per language
TIME_PERIOD = "daily" # Optional: Set trending period -> 'daily', 'weekly', or 'monthly'

# = }}}

####################
# SCRAPE FUNCTIONS #
####################

# = {{{

def scrape_github_trending(language, limit, since="daily"):
    """Scrapes the top N trending repositories for a given language."""
    url = f"https://github.com/trending/{language}?since={since}"
    
    # Custom User-Agent header to avoid being blocked by default requests headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching page for '{language}': {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    repo_rows = soup.find_all("article", class_="Box-row")
    
    results = []
    
    for row in repo_rows[:limit]:
        # Extract repository name & URL
        h2_tag = row.find("h2", class_="h3")
        if not h2_tag or not h2_tag.find("a"):
            continue
            
        # Url Formatting
        repo_link = h2_tag.find("a")
        relative_path = repo_link.get("href", "").strip()
        repo_name = "".join(relative_path.split())          # Clean up whitespace/newlines
        # full_url = f"https://github.com{relative_path}"
        
        # Extract description
        p_tag = row.find("p", class_="col-9")
        description = p_tag.text.strip() if p_tag else "No description provided."
        
        # Extract total stars count
        stars_tag = row.find("a", href=lambda h: h and h.endswith("/stargazers"))
        stars = stars_tag.text.strip() if stars_tag else "N/A"
        
        # Extract period stars gained (e.g. "120 stars today")
        stars_today_tag = row.find("span", class_="float-sm-right")
        stars_today = stars_today_tag.text.strip() if stars_today_tag else "N/A"


            # "url": full_url, # Didn't like how it shows, plus I can't click it on paper
        results.append({
            "name": repo_name,
            "description": description,
            "stars": stars,
            "period_stars": stars_today
        })
        
    return results

def main():
    # print(f"--- Fetching Top {NUM_REPOS} Trending Repositories ({TIME_PERIOD.capitalize()}) ---\n")
    
    all_data = {}
    
    for lang in LANGUAGES:
        # Normalize language slug for URLs (e.g., C++ -> c++)
        url_lang = lang.lower().replace(" ", "-")
        # print(f"Fetching trending repos for: '{lang}'...")
        
        repos = scrape_github_trending(url_lang, NUM_REPOS, TIME_PERIOD)
        all_data[lang] = repos
        
        # Polite delay between requests to be respectful to GitHub's servers
        time.sleep(1)

    # Output Results
    print("\n" + "=" * 60)
    for lang, repos in all_data.items():
        print(f"\n### TOP {NUM_REPOS} TRENDING IN: {lang.upper()}")
        print("-" * 60)
        
        if not repos:
            print("No repositories found or an error occurred.")
            continue
            
        for i, repo in enumerate(repos, start=1):
            print(f"{i}. {repo['name']}")
            print(f"   Stars: {repo['stars']} | Growth: {repo['period_stars']}")
            print(f"   Desc: {repo['description']}\n")
            # print(f"   URL: {repo['url']}")

# = }}}

if __name__ == "__main__":
    main()
