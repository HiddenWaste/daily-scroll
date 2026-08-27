import datetime
import os
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

# = }}}

####################
# SCRAPE FUNCTIONS #
####################

# = {{{
def run_script_and_capture_output(script_name: str) -> str:
    """Runs a Python script and captures its stdout and stderr."""
    if not os.path.exists(script_name):
        return f"[Error: Script '{script_name}' not found in current directory.]"

    try:
        result = subprocess.run(
            [sys.executable, script_name],
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


def generate_pdf(sections: list, output_filename: str):
    """Converts ANSI text outputs into styled HTML optimized for Kindle devices."""
    conv = Ansi2HTMLConverter(inline=True, dark_bg=False)
    today_str = datetime.datetime.now().strftime("%B %d, %Y")

    html_sections = []
    for section in sections:
        title = section["title"]
        raw_text = section["output"]

        # Convert ANSI colors/formatting into inline styled HTML spans
        formatted_html = conv.convert(raw_text, full=False)

        html_sections.append(
            f"""
        <div class="section">
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

        print(f" -> Running {script}...")
        output = run_script_and_capture_output(script)
        collected_data.append({"title": title, "output": output})

    print(f"📄 Compiling outputs into '{OUTPUT_PDF}'...")
    generate_pdf(collected_data, OUTPUT_PDF)
    print(f"✨ Local PDF generated successfully: {OUTPUT_PDF}")

    # Check and sync to Kindle if connected via USB
    sync_to_kindle(OUTPUT_PDF, KINDLE_DIR)


if __name__ == "__main__":
    main()
    
# = }}}
