import datetime
import os
import re
import shutil
import subprocess
import sys
from ansi2html import Ansi2HTMLConverter
from weasyprint import HTML

#################
# CONFIGURATION #
#################

# = {{{

# List of target scripts to execute and compile into the PDF
TARGET_SCRIPTS = [
    {
        "title": "Calendar Schedule",
        "script": "gcal_today.py",
    },
    {
        "title": "GitHub Trending Repositories",
        "script": "gh.py",
    },
    {
        "title": "Terminal Trove: Tool of the Week",
        "script": "terminal-trove.py",
    },
]

OUTPUT_PDF = "daily_scroll.pdf"
KINDLE_DIR = "/media/compy/Kindle/documents/"
SCRAPER_DIR = "./scrapers/"

# = }}}

####################
# SCRAPE FUNCTIONS #
####################

# = {{{
def run_script_and_capture_output(script_name: str) -> str:
    """Runs a Python script inside SCRAPER_DIR and captures stdout/stderr."""
    script_path = os.path.join(SCRAPER_DIR, script_name)

    if not os.path.exists(script_path):
        return f"[Error: Script '{script_name}' not found at path '{script_path}'.]"

    try:
        # Run script with cwd set to SCRAPER_DIR so local imports/credentials work seamlessly
        result = subprocess.run(
            [sys.executable, os.path.basename(script_path)],
            cwd=SCRAPER_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout
        if result.stderr:
            output += f"\n--- STDERR ---\n{result.stderr}"

        return (
            output.strip()
            if output.strip()
            else "[Script executed successfully with no output.]"
        )
    except subprocess.TimeoutExpired:
        return f"[Error: Script '{script_name}' timed out.]"
    except Exception as e:
        return f"[Error running '{script_name}': {e}]"


def split_github_output_by_language(raw_text: str) -> list[dict]:
    """Splits output from gh.py into separate section entries for each language."""
    # Matches headers like "### TOP 5 TRENDING IN: PYTHON"
    pattern = r"(### TOP \d+ TRENDING IN: [^\n]+)"
    parts = re.split(pattern, raw_text)

    # If parsing doesn't find language headers, fall back to returning raw text
    if len(parts) <= 1:
        return [{"title": "GitHub Trending Repositories", "output": raw_text}]

    sections = []
    # If there is preamble text before the first heading, include it
    if parts[0].strip():
        sections.append({"title": "GitHub Trending Overview", "output": parts[0].strip()})

    # Step through matched headings and content pairs
    for i in range(1, len(parts), 2):
        header = parts[i].replace("###", "").strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections.append({"title": header, "output": f"{header}\n{body}"})

    return sections


def generate_pdf(sections: list, output_filename: str):
    """Converts ANSI text outputs into styled HTML optimized for Kindle devices."""
    conv = Ansi2HTMLConverter(inline=True, dark_bg=False)
    today_str = datetime.datetime.now().strftime("%B %d, %Y")

    html_sections = []
    for section in sections:
        title = section["title"]
        raw_text = section["output"]
        page_break = section.get("page_break_after", False)

        # Convert ANSI colors/formatting into inline styled HTML spans
        formatted_html = conv.convert(raw_text, full=False)

        break_class = " page-break-after" if page_break else ""

        html_sections.append(
            f"""
        <div class="section{break_class}">
            <h2 class="section-header">{title}</h2>
            <pre class="terminal-output">{formatted_html}</pre>
        </div>
        """
        )

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>The Daily Scroll - {today_str}</title>
        <style>
            @page {{
                size: A4;
                margin: 0.8cm;
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-family: monospace;
                    font-size: 11pt;
                    color: #444;
                }}
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                color: #000;
                line-height: 1.5;
                margin: 0;
                padding: 0;
            }}
            .header {{
                border-bottom: 2px solid #000;
                padding-bottom: 6px;
                margin-bottom: 16px;
            }}
            .title {{
                font-size: 28pt;
                font-weight: bold;
                margin: 0;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .date {{
                font-size: 14pt;
                color: #333;
                font-weight: bold;
                display: block;
                margin-top: 4px;
            }}
            .section {{
                margin-bottom: 24px;
            }}
            
            /* Forces page break between specific items like GitHub language sections */
            .page-break-after {{
                page-break-after: always;
            }}
            
            .section-header {{
                font-size: 18pt;
                font-weight: bold;
                text-transform: uppercase;
                border-bottom: 2px solid #555;
                margin-top: 18px;
                margin-bottom: 10px;
                padding-bottom: 4px;
                color: #000;
            }}
            .terminal-output {{
                background-color: #f4f4f4;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 12px 14px;
                font-family: "Courier New", Courier, monospace;
                font-size: 12.5pt;
                line-height: 1.45;
                white-space: pre-wrap;
                word-wrap: break-word;
                margin: 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">The Daily Scroll</h1>
            <span class="date">{today_str}</span>
        </div>
        {"".join(html_sections)}
    </body>
    </html>
    """

    HTML(string=full_html).write_pdf(output_filename)


def sync_to_kindle(source_pdf: str, kindle_dir: str):
    """Safely copies the generated PDF to the Kindle documents directory if mounted."""
    if os.path.exists(kindle_dir) and os.path.isdir(kindle_dir):
        destination = os.path.join(kindle_dir, os.path.basename(source_pdf))
        try:
            shutil.copy2(source_pdf, destination)
            print(f"📖 Kindle detected! Successfully copied to {destination}")
        except Exception as e:
            print(f"⚠️ Kindle folder exists, but failed to copy file: {e}")
    else:
        print(f"ℹ️ Kindle not detected at '{kindle_dir}'. Skipping Kindle transfer.")

# = }}}

########
# MAIN #
########

# = {{{

def main():
    print("🚀 Gathering output from scripts...")
    collected_data = []

    for item in TARGET_SCRIPTS:
        title = item["title"]
        script = item["script"]

        print(f" -> Running {script} from {SCRAPER_DIR}...")
        output = run_script_and_capture_output(script)

        # Special handling for gh.py to break each language onto its own page
        if script == "gh.py":
            gh_sections = split_github_output_by_language(output)
            for idx, gh_sec in enumerate(gh_sections):
                # Mark page_break_after = True for all language blocks except the last one
                is_last = idx == len(gh_sections) - 1
                gh_sec["page_break_after"] = not is_last
                collected_data.append(gh_sec)
        else:
            collected_data.append({"title": title, "output": output})

    print(f"📄 Compiling outputs into '{OUTPUT_PDF}'...")
    generate_pdf(collected_data, OUTPUT_PDF)
    print(f"✨ Local PDF generated successfully: {OUTPUT_PDF}")

    # Check and sync to Kindle if connected via USB
    sync_to_kindle(OUTPUT_PDF, KINDLE_DIR)


if __name__ == "__main__":
    main()

# = }}}
