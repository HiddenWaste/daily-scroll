from urllib.parse import urljoin
from bs4 import BeautifulSoup
from curl_cffi import requests

####################
# SCRAPE FUNCTIONS #
####################

# = {{{
def get_terminal_trove_tool_of_the_week():
  url = "https://terminaltrove.com/"

  try:
    response = requests.get(url, impersonate="chrome", timeout=10)
    response.raise_for_status()
  except Exception as e:
    print(f"Error fetching Terminal Trove: {e}")
    return None

  soup = BeautifulSoup(response.text, "html.parser")

  # Find heading for "Terminal Tool of The Week"
  heading = soup.find(
      lambda tag: tag.name in ["h2", "h3", "h4"]
      and "Terminal Tool of The Week" in tag.text
  )
  if not heading:
    heading = soup.find(
        string=lambda text: text and "Terminal Tool of The Week" in text
    )
    if heading:
      heading = heading.parent

  if not heading:
    print("Could not locate the 'Terminal Tool of The Week' section.")
    return None

  # Find the container anchor link
  tool_section = heading.find_next(["a", "div"])
  tool_link = (
      tool_section if tool_section.name == "a" else tool_section.find("a")
  )

  if not tool_link:
    print("Found section header, but couldn't locate tool details.")
    return None

  # Safely construct the absolute URL using urljoin
  raw_href = tool_link.get("href", "")
  full_url = urljoin("https://terminaltrove.com", raw_href)

  # Extract tool title (typically in h3/h4 or strong inside the link)
  title_tag = tool_link.find(["h3", "h4", "h5", "strong"])
  if title_tag:
    name_text = title_tag.text.strip()
  else:
    # Fallback to the first non-empty text line
    lines = [line.strip() for line in tool_link.text.splitlines() if line.strip()]
    name_text = lines[0] if lines else "Unknown Tool"

  # Extract description
  desc_tag = tool_link.find("p")
  desc_text = (
      desc_tag.text.strip() if desc_tag else "No description available."
  )

  return {"name": name_text, "url": full_url, "description": desc_text}

# = }}}

########
# MAIN #
########

# = {{{
if __name__ == "__main__":
  print("Fetching the current Tool of the Week from Terminal Trove...\n")
  tool = get_terminal_trove_tool_of_the_week()

  if tool:
    print("=" * 50)
    print(f"🛠️  TOOL OF THE WEEK: {tool['name']}")
    print("=" * 50)
    # print(f"URL:         {tool['url']}")
    print(f"Description: {tool['description']}")

# = }}}
