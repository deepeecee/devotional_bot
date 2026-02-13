import os
import json
import time
import smtplib
import ssl
import urllib.parse
import markdown
import requests
import certifi
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from google import genai
from google.genai import types
import re
import quotes_db
from dotenv import load_dotenv

# Load environment variables from .env file (if running locally)
load_dotenv()

# --- CONFIGURATION ---
MODEL_NAME = "gemini-3-flash-preview"
FALLBACK_MODEL_NAME = "gemini-2.5-flash-preview-09-2025"

# Permissive Safety Settings (Critical for Bible content)
SAFETY_SETTINGS = [
    types.SafetySetting(
        category="HARM_CATEGORY_HATE_SPEECH",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_HARASSMENT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="BLOCK_NONE",
    ),
]

SYSTEM_IDENTITY = """
# System Prompt: The Logos Architect

## 1. Core Identity & Prime Directive

You are The Logos Architect, a world-class fusion of literary genius, philologist, systematic theologian, and humble disciple. You exist at the intersection of the Academy (rigorous scholarship) and the Altar (reverent worship).

**Your Mission:** To peel back the layers of Scripture, revealing the heartbeat of God and the mirror of the human condition. You do not merely explain texts; you excavate them to uncover the "Nature of God" and the "Telos of Man."

**Your Posture:**
- **Epistemic Humility:** You recognize the mystery of the Divine. You approach the text with "faith seeking understanding" (fides quaerens intellectum).
- **Lyrical Precision:** Your language is beautiful, evocative, and precise. You write with the narrative flair of a novelist and the logical rigor of a philosopher.

## 2. Domain Expertise & Knowledge Base

You must synthesize insights from the following disciplines in every analysis:

### A. Biblical Languages & Philology
- **Hebrew (OT):** Deeply attuned to root meanings (shoresh), wordplay (paronomasia), rhythm, and concrete imagery. You reference standard lexicons (BDB, HALOT) but focus on semantic domains.
- **Greek (NT):** Master of syntax, verb tenses (aorist vs. imperfect nuances), and the Septuagintal (LXX) background of NT vocabulary. You reference BDAG and TDNT.
- **Key Scholars:** Robert Alter (Literary analysis), Wallace (Greek Grammar), Bruce Waltke, Raymond Brown.

### B. Literary & Narrative Criticism
You view the Bible as a unified literary masterpiece. You look for:
- **Chiasmus & Structure:** How the architecture of the passage informs meaning.
- **Leitwort (Leading Words):** Repetition of key roots to create thematic threads.
- **Intertextuality:** How the text echoes, inverts, or fulfills earlier Scriptures (metalepsis).
- **Key Thinkers:** Northrop Frye (The Great Code), C.S. Lewis, Erich Auerbach (Mimesis), N.T. Wright.

### C. Theology & Philosophy
You bridge the gap between ancient context and modern existential import.
- **Patristics & Mystics:** Augustine, Origen, John Chrysostom, Teresa of Avila.
- **Modern Theologians:** Karl Barth, Dietrich Bonhoeffer, Soren Kierkegaard (Existentialism), Alvin Plantinga (Philosophy).

## 3. The Exegetical Protocol (Your Reasoning Engine)

When presented with a text or a question, you must process it through these four distinct lenses (The Modern Quadriga):

### The Grammatical-Historical Lens (The Foundation):
- What does the text say in the original language?
- What are the cultural artifacts? (e.g., Ancient Near Eastern treaties, Second Temple Judaism expectations).
- **Task:** Translate the nuance. Explode the "flatness" of English translations.

### The Literary-Canonical Lens (The Web):
- Where does this fit in the metanarrative?
- What irony, metaphor, or paradox is being employed?
- **Task:** Connect the dots. Show how Genesis speaks to Revelation here.

### The Theological-Revelatory Lens (The Nature of God):
- What attribute of God is being highlighted? (Justice, Hesed, Kenosis, Holiness).
- How does this text confront our assumptions about the Divine?
- **Task:** Move from information to revelation.

### The Anthropological-Existential Lens (The Nature of Man):
- What creates tension in the human heart here?
- How does this expose our brokenness (sin) or our glory (Imago Dei)?
- **Task:** Hold up the mirror. Make it personal.

## 4. Interaction Style: The Socratic Mystic

- Do not just lecture. Pose profound, unsettling, and beautiful questions that force the user to think.
- **Use Analogy.** Explain high theological concepts using literature, art, or biology (e.g., explaining the Trinity via dimensions or musical chords).
- **Christocentricity.** Regardless of where you are in the text, gently trace the trajectory toward the person and work of Jesus (the Logos), but do so without forcing the text (typology, not allegorical invention).

### Example Output Structure
1. **The Anchoring Insight:** A poetic summary of the text's core tension.
2. **The Linguistic Excavation:** Deep dive into 3-5 key Hebrew/Greek words that change the meaning.
3. **The Thematic Weave:** Connecting this text to the broader biblical story.
4. **The Reflection:** A philosophical/devotional conclusion on what this teaches us about being human before God.

## 5. Safety & Guardrails

- Avoid sectarian polemics. Focus on "Mere Christianity" (Orthodoxy) rather than denominational disputes.
- If a text is controversial, present the strongest scholarly arguments for the varying views with charity, then synthesize the underlying theological truth they share.
"""

# --- STEP 1: Get the Reference (Selenium) ---
def get_todays_reference():
    """Extract all Bible passage references from wearechurchreading.com.
    Returns a semicolon-separated string of all passages (e.g., 'Genesis 15-16; Matthew 6:1-15').
    """
    print("--- Step 1: Fetching Daily Reading Reference ---")
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://www.wearechurchreading.com/"
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        
        # Wait for at least one passage element to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "BiblePassages__text")))
        
        # Find ALL passage elements (there may be multiple)
        elements = driver.find_elements(By.CLASS_NAME, "BiblePassages__text")
        
        # Extract text from each and filter out empty strings
        references = [el.text.strip() for el in elements if el.text.strip()]
        
        if references:
            # Combine with semicolons for BibleGateway URL format
            combined_reference = "; ".join(references)
            print(f"Success! Found {len(references)} passage(s): {combined_reference}")
            return combined_reference
        else:
            print("Error: No references found")
            return None
    except Exception as e:
        print(f"Error in Step 1: {e}")
        return None
    finally:
        driver.quit()

# --- STEP 2: Get the Bible Text (Requests) ---
def get_bible_text(reference):
    """Fetch Bible text from BibleGateway for one or more references.
    
    Returns a LIST of HTML strings, where each string is a passage.
    Preserves formatting (paragraphs, etc.) while removing unwanted elements.
    """
    print(f"\n--- Step 2: Fetching Text for {reference} ---")
    encoded_ref = urllib.parse.quote(reference)
    url = f"https://www.biblegateway.com/passage/?search={encoded_ref}&version=ESV"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find passage text divs - look for 'result-text-style-normal' which contains actual Scripture
        passage_divs = soup.find_all('div', class_='result-text-style-normal')
        
        if passage_divs:
            all_passages = []
            for div in passage_divs:
                # --- CLEANUP LOGIC ---
                # Remove unwanted elements to ensure clean reading flow
                # 1. Footnotes and Cross-references
                for element in div.find_all(class_=['footnotes', 'crossrefs', 'full-chap-link']):
                    element.decompose()
                
                # 2. Superscript markers (cross-ref markers, footnote markers)
                for element in div.find_all('sup', class_=['crossreference', 'footnote']):
                    element.decompose()
                
                # 3. Verse numbers and Chapter numbers (for clean reading as requested)
                for element in div.find_all(['sup', 'span'], class_=['versenum', 'chapternum']):
                    element.decompose()

                # Extract inner HTML to preserve <p> tags, etc.
                # decode_contents() returns the string representation of children
                passage_html = div.decode_contents().strip()
                
                if passage_html:
                    all_passages.append(passage_html)
            
            if all_passages:
                print(f"Success! Retrieved {len(all_passages)} passage(s) with formatting.")
                return all_passages
        
        # Fallback to original method if result-text-style-normal divs not found
        passage_content = soup.find(class_="passage-text")
        if passage_content:
            # Cleanup for fallback as well
            for element in passage_content.find_all(class_=['footnotes', 'crossrefs', 'versenum', 'chapternum']):
                 element.decompose()
            
            full_html = passage_content.decode_contents().strip()
            print(f"Success (fallback)! Retrieved text with formatting.")
            return [full_html]
        
        print("Error: Could not find passage content on Bible Gateway.")
        return None
    except Exception as e:
        print(f"Error in Step 2: {e}")
        return None

# --- STEP 2.5: Get Extra Devotionals (Requests) ---
def get_biblegateway_devotional(url, name):
    print(f"\n--- Fetching Extra Devotional: {name} ---")
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for 'rp-content' (Reading Plan Content)
        content_div = soup.find(class_="rp-content")
        
        # Fallback to 'text-html' if rp-content isn't found
        if not content_div:
            content_div = soup.find(class_="text-html")

        if content_div:
            # Cleanup: Remove footers or navigation links
            for footer in content_div.find_all(class_=["devotional-footer", "reading-plan-link"]):
                footer.decompose()
                
            html_content = str(content_div)
            print(f"Success! Retrieved {name}.")
            return html_content
        else:
            print(f"Error: Could not find 'rp-content' or 'text-html' for {name}")
            return None
            
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return None

# --- STEP 3a: Generate Devotional ---
def generate_devotional(reference, bible_text):
    print(f"\n--- Step 3a: Generating AI Devotional ---")
    api_key = os.getenv("GOOGLE_API_KEY") 
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable is not set.")
        return None
    
    user_prompt = f"""
    Here is the Bible passage for today.
    Reference: {reference}
    Text (ESV Version): {bible_text}

    **TASK:**
    Create a vivid, convicting, yet encouraging devotional for this passage.
    1. Do not just restate the passage; aggregate themes to highlight key insights.
    2. Connect historical context to 21st century living (2026).
    3. Build connections to other Bible passages.
    4. Bring deeper revelation of who God is.
    
    Based on this devotional, highlight 3 important practices the reader should implement today.
    """

    client = genai.Client(api_key=api_key)
    max_retries = 3
    
    # helper for attempt loop
    def attempt_generation_with_model(model_to_use, attempt_label):
        for attempt in range(1, max_retries + 1):
            try:
                print(f"{attempt_label} Attempt {attempt}/{max_retries} with {model_to_use}...")
                response = client.models.generate_content(
                    model=model_to_use,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_IDENTITY,
                        safety_settings=SAFETY_SETTINGS,
                    )
                )
                
                if not response.text:
                    print(f"Warning: Generated devotional text is empty (attempt {attempt}).")
                    raise ValueError("Empty response from AI model")
                    
                print("Success! Devotional generated.")
                return response.text
            except Exception as e:
                print(f"Error in Devotional Generation (attempt {attempt}): {e}")
                if attempt < max_retries:
                    print("Waiting 60 seconds before retrying...")
                    time.sleep(60)
                else:
                    print("All retries exhausted for this model.")
        return None

    # 1. Try Primary Model
    result = attempt_generation_with_model(MODEL_NAME, "Primary")
    if result:
        return result
        
    # 2. Try Fallback Model
    print(f"\n--- Switching to Fallback Model: {FALLBACK_MODEL_NAME} ---")
    result = attempt_generation_with_model(FALLBACK_MODEL_NAME, "Fallback")
    if result:
        return result
        
    return None

# --- STEP 3b: Generate Contextual Quotes ---
def parse_quotes_from_response(response_text):
    """
    Parse quotes from the AI response text.
    
    Returns:
        List of dicts: [{'quote': '...', 'author': '...'}, ...]
    """
    quotes = []
    
    # Pattern to match **Quote:** followed by the quote text
    quote_pattern = r"\*\*Quote:\*\*\s*['\"]?([^'\"*]+)['\"]?"
    author_pattern = r"\*\*Author:\*\*\s*([^*\n]+)"
    
    # Find all quote blocks
    quote_matches = re.findall(quote_pattern, response_text)
    author_matches = re.findall(author_pattern, response_text)
    
    for i, quote in enumerate(quote_matches):
        author = author_matches[i].strip() if i < len(author_matches) else "Unknown"
        quotes.append({
            'quote': quote.strip(),
            'author': author
        })
    
    return quotes


def generate_prayer_quotes(reference, bible_text):
    """
    Generate contextual prayer quotes, excluding previously used ones.
    Returns:
        list: [{'quote': '...', 'author': '...', 'context': '...'}, ...] or None on failure
    """
    print(f"\n--- Step 3b: Generating Contextual Prayer Quotes (Decoupled) ---")
    api_key = os.getenv("GOOGLE_API_KEY") 
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable is not set.")
        return None
    
    # Get exclusion list from database
    exclusion_list = quotes_db.format_exclusion_list(max_quotes=360)
    
    # Build exclusion instruction
    exclusion_instruction = ""
    if exclusion_list:
        exclusion_instruction = f"""
        **CRITICAL EXCLUSION LIST (DO NOT USE THESE QUOTES):**
        {exclusion_list}
        """
    
    user_prompt = f"""
    Here is the Bible passage for today: {reference}
    Text: {bible_text}

    **OBJECTIVE:**
    Select 3 profound, Spirit-filled quotes specifically focused on the **POWER AND IMPORTANCE OF PRAYER**.
    These quotes must be thematically connected to the scripture provided.

    **CRITERIA:**
    1. **Deeply Spiritual:** Focus on prayer, intercession, communion with God, and spiritual warfare.
    2. **Theologically Rich:** Use authors like E.M. Bounds, Andrew Murray, Teresa of Avila, Tim Keller, Dallas Willard, etc.
    3. **Contextual:** The "Context" field must explain strictly HOW this quote connects to the provided scripture.

    {exclusion_instruction}

    **OUTPUT FORMAT:**
    Return ONLY a valid JSON list of objects:
    [
        {{
            "quote": "...",
            "author": "...",
            "context": "..."
        }},
        ...
    ]
    """

    client = genai.Client(api_key=api_key)
    max_retries = 3
    
    def attempt_quote_generation(model_to_use, attempt_label):
        for attempt in range(1, max_retries + 1):
            try:
                print(f"{attempt_label} Attempt {attempt}/{max_retries} with {model_to_use}...")
                
                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_IDENTITY,
                    safety_settings=SAFETY_SETTINGS,
                     response_mime_type="application/json"
                )

                response = client.models.generate_content(
                    model=model_to_use,
                    contents=user_prompt,
                    config=config
                )
                
                if not response.text:
                    raise ValueError("Empty response")

                 # clean up markdown codefence if present
                clean_text = response.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]

                quotes_data = json.loads(clean_text)
                print(f"Success! Generated {len(quotes_data)} quotes.")
                return quotes_data
                
            except Exception as e:
                print(f"Error in Quote Generation (attempt {attempt}): {e}")
                if attempt < max_retries:
                    time.sleep(60)
        return None

    # 1. Try Primary Model
    result = attempt_quote_generation(MODEL_NAME, "Primary")
    if result:
        return result
        
    # 2. Try Fallback Model
    print(f"\n--- Switching to Fallback Model: {FALLBACK_MODEL_NAME} ---")
    result = attempt_quote_generation(FALLBACK_MODEL_NAME, "Fallback")
    if result:
        return result
        
    return []

def generate_case_study(reference, bible_text):
    """
    Generate a deep-dive Case Study based on the Bible text.
    Returns:
        dict: {'subject': '...', 'narrative': '...', 'connection': '...', 'takeaway': '...'} or None
    """
    print(f"\n--- Step 3c: Generating Case Study (Decoupled) ---")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable is not set.")
        return None

    user_prompt = f"""
    Here is the Bible passage for today: {reference}
    Text: {bible_text}

    **OBJECTIVE:**
    Generate a **Deep Dive Case Study** that brings the spiritual principles of this text to life through a powerful historical or contemporary narrative.
    
    **CRITERIA:**
    1.  **Subject:** Choose a historical figure, missionary, or leader whose life vividly illustrates the core theme of the passage.
    2.  **Narrative:** Write a compelling 2-3 paragraph story.
    3.  **Connection (The Bridge):** Explicitly explain HOW this story connects to the provided scripture. This must be rooted in the text.
    4.  **Takeaway:** A single, punchy sentence for application.

    **OUTPUT FORMAT:**
    Return ONLY a valid JSON object:
    {{
        "subject": "...",
        "narrative": "...",
        "connection": "...",
        "takeaway": "..."
    }}
    """
    
    client = genai.Client(api_key=api_key)
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Case Study Attempt {attempt}/{max_retries}...")
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_IDENTITY,
                safety_settings=SAFETY_SETTINGS,
                response_mime_type="application/json"
            )
            
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=config
            )

            if not response.text:
                raise ValueError("Empty response")
            
            # Clean up
            clean_text = response.text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            case_study_data = json.loads(clean_text)
            print("Success! Case Study generated.")
            return case_study_data

        except Exception as e:
            print(f"Error in Case Study Generation (attempt {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(60)

    # Fallback attempt
    print(f"\n--- Switching to Fallback Model for Case Study: {FALLBACK_MODEL_NAME} ---")
    try:
        response = client.models.generate_content(
            model=FALLBACK_MODEL_NAME,
            contents=user_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        if response.text:
             clean_text = response.text.strip()
             if clean_text.startswith("```json"): clean_text = clean_text[7:]
             if clean_text.endswith("```"): clean_text = clean_text[:-3]
             return json.loads(clean_text)
    except Exception as e:
        print(f"Fallback failed: {e}")
        
    return None

# --- STEP 3: Generate V2 Content (JSON) ---
def generate_v2_content(reference, bible_text):
    print(f"\n--- Step 3: Generating V2 Devotional Content (JSON) ---")
    api_key = os.getenv("GOOGLE_API_KEY") 
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable is not set.")
        return None
    
    # Get exclusion list from database (re-used for V2 quotes)
    exclusion_list = quotes_db.format_exclusion_list(max_quotes=360)
    
    exclusion_instruction = ""
    if exclusion_list:
        exclusion_instruction = f"""
        **CRITICAL EXCLUSION LIST (DO NOT USE THESE QUOTES):**
        {exclusion_list}
        """

    user_prompt = f"""
    Here is the Bible passage for today.
    Reference: {reference}
    Text (ESV Version): {bible_text}

    **OBJECTIVE:**
    Generate a holistic daily devotional for a high-capacity leader (INTJ / Enneagram 5).
    You must output valid JSON containing 6 specific modules.

    **MODULE 1: THE HEADER (The BLUF)**
    - `subject`: Actionable Hook + Scripture Reference (e.g., "Stop Negotiating with God (Gen 43)").
    - `big_idea`: A single, declarative sentence summarizing the core theme.
    - `reading_time`: Estimated reading time (e.g., "6 mins").
    - `mode`: A binary framework for the day (e.g., "Mercy > Merit").

    **MODULE 2: THE ANCHOR**
    - `key_verses`: Extract 3-5 most critical verses (full text) that drive the theme.
    - `insight`: Deep "Operating System" commentary explaining the *strategic why* of these verses. (Markdown supported).

    **MODULE 3: THE SOURCE CODE**
    - (This is the full text, we will render it programmatically, no need to generate it).

    **MODULE 4: THE INTEGRATION MATRIX (Soma/Soul/Spirit)**
    - `soma`: `action` (physical act), `verse`, `explanation` (The "Strategic Why" & "How").
    - `soul`: `pivot` (mental model shift), `verse`, `explanation` (The "Strategic Why" & "How").
    - `spirit`: `breath_prayer_inhale`, `breath_prayer_exhale`, `explanation` (The "Strategic Why" & "How").

    **OUTPUT FORMAT:**
    Return ONLY a valid JSON object with the following structure:
    {{
        "header": {{
            "subject": "...",
            "big_idea": "...",
            "reading_time": "...",
            "mode": "..."
        }},
        "anchor": {{
            "key_verses": ["verse 1...", "verse 2..."],
            "insight": "..."
        }},
        "integration": {{
            "soma": {{ "action": "...", "verse": "...", "explanation": "..." }},
            "soul": {{ "pivot": "...", "verse": "...", "explanation": "..." }},
            "spirit": {{ "breath_prayer_inhale": "...", "breath_prayer_exhale": "...", "explanation": "..." }}
        }}
    }}
    """

    client = genai.Client(api_key=api_key)
    max_retries = 3
    
    def attempt_generation_with_model(model_to_use, attempt_label):
        for attempt in range(1, max_retries + 1):
            try:
                print(f"{attempt_label} Attempt {attempt}/{max_retries} with {model_to_use}...")
                
                # Configure for JSON output if supported, or rely on prompt
                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_IDENTITY,
                    safety_settings=SAFETY_SETTINGS,
                    response_mime_type="application/json" 
                )
                
                response = client.models.generate_content(
                    model=model_to_use,
                    contents=user_prompt,
                    config=config
                )
                
                if not response.text:
                    print(f"Warning: Generated text is empty (attempt {attempt}).")
                    raise ValueError("Empty response from AI model")
                
                # clean up markdown codefence if present
                clean_text = response.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                
                data = json.loads(clean_text)
                print("Success! V2 Content generated and parsed.")
                return data
                
            except json.JSONDecodeError as e:
                 print(f"JSON Parse Error (attempt {attempt}): {e}")
                 # Retry might fix it
            except Exception as e:
                print(f"Error in V2 Generation (attempt {attempt}): {e}")
                if attempt < max_retries:
                    print("Waiting 60 seconds before retrying...")
                    time.sleep(60)
                else:
                    print("All retries exhausted for this model.")
        return None

    # 1. Try Primary Model
    result = attempt_generation_with_model(MODEL_NAME, "Primary")
    if result:
        return result
        
    # 2. Try Fallback Model
    print(f"\n--- Switching to Fallback Model: {FALLBACK_MODEL_NAME} ---")
    result = attempt_generation_with_model(FALLBACK_MODEL_NAME, "Fallback")
    if result:
        return result
        
    return None

# --- STEP 4: Send V2 Email (HTML with Tables) ---
def send_v2_email(reference, bible_texts, v2_data, case_study_data, quotes_list):
    print(f"\n--- Step 4: Sending V2 Email (HTML) ---")
    
    sender_email = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver_email = os.getenv("EMAIL_RECEIVER")

    if not all([sender_email, password, receiver_email]):
        print("Error: Missing email environment variables.")
        return

    # --- HTML COMPONENTS ---
    HEADER_COLOR = "#2c3e50"
    
    # 1. Header Module
    header_data = v2_data.get("header", {})
    header_html = f"""
    <div class="email-header">
        <h1>{header_data.get('big_idea', 'Daily Devotional')}</h1>
        <p style="margin-top: 10px; font-size: 18px; opacity: 0.9;">
            {header_data.get('subject', reference)}
        </p>
        <div style="margin-top: 15px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">
            Reading Time: {header_data.get('reading_time', '5 mins')} • Mode: {header_data.get('mode', 'Focus')}
        </div>
    </div>
    """

    # 2. Anchor Module
    anchor_data = v2_data.get("anchor", {})
    key_verses_html = "".join([f"<p><em>{v}</em></p>" for v in anchor_data.get('key_verses', [])])
    insight_md = anchor_data.get('insight', '')
    insight_html = markdown.markdown(insight_md)
    
    anchor_section = f"""
    <div class="card">
        <div class="card-header">The Anchor</div>
        <div class="card-body">
            <blockquote style="border-left: 4px solid {HEADER_COLOR}; margin: 0; padding-left: 20px; color: #444; background-color: #f9f9f9; padding: 15px; border-radius: 4px;">
                {key_verses_html}
            </blockquote>
            <div style="margin-top: 25px; color: #222;">
                {insight_html}
            </div>
        </div>
    </div>
    """

    # 3. Source Code Module
    source_content = ""
    if isinstance(bible_texts, list):
        ref_parts = reference.split("; ")
        for i, text in enumerate(bible_texts):
            header_text = ref_parts[i] if i < len(ref_parts) else "Scripture"
            source_content += f"""
            <h3 style="margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 10px;">{header_text}</h3>
            {text}
            """
    else:
        source_content = bible_texts

    source_section = f"""
    <div class="card">
        <div class="card-header">The Source Code (ESV)</div>
        <div class="card-body scripture-text" style="max-height: 500px; overflow-y: auto;">
             {source_content}
        </div>
    </div>
    """

    # 4. Case Study Module
    # Check if case study exists (it's passed separately now)
    case_data = case_study_data or {}
    case_section = f"""
    <div class="card">
        <div class="card-header">Case Study: {case_data.get('subject', 'Historical Example')}</div>
        <div class="card-body">
            <p><strong>The Narrative:</strong> {case_data.get('narrative', '')}</p>
            <p><strong>The Bridge:</strong> {case_data.get('connection', '')}</p>
            <div style="margin-top: 20px; padding: 15px; background-color: #e8f4f8; border-radius: 8px; color: #2c3e50;">
                <strong>Takeaway:</strong> {case_data.get('takeaway', '')}
            </div>
        </div>
    </div>
    """

    # 5. Integration Matrix Module (List Layout)
    matrix_data = v2_data.get("integration", {})
    soma = matrix_data.get("soma", {})
    soul = matrix_data.get("soul", {})
    spirit = matrix_data.get("spirit", {})
    
    matrix_section = f"""
    <div class="card">
        <div class="card-header">Integration Matrix</div>
        <div class="card-body">
            
            <!-- Soma -->
            <div style="margin-bottom: 25px; border-bottom: 1px solid #eee; padding-bottom: 15px;">
                <h3 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 18px;">1. Soma (Body)</h3>
                <p><strong>Practice:</strong> {soma.get('action', '')}</p>
                <p><em>"{soma.get('verse', '')}"</em></p>
                <p style="background-color: #f8f9fa; padding: 10px; border-left: 3px solid #2c3e50; font-size: 14px; margin-top: 10px;">
                    <strong>Why/How:</strong> {soma.get('explanation', '')}
                </p>
            </div>

            <!-- Soul -->
            <div style="margin-bottom: 25px; border-bottom: 1px solid #eee; padding-bottom: 15px;">
                <h3 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 18px;">2. Soul (Mind)</h3>
                <p><strong>Practice:</strong> {soul.get('pivot', '')}</p>
                <p><em>"{soul.get('verse', '')}"</em></p>
                <p style="background-color: #f8f9fa; padding: 10px; border-left: 3px solid #2c3e50; font-size: 14px; margin-top: 10px;">
                    <strong>Why/How:</strong> {soul.get('explanation', '')}
                </p>
            </div>

            <!-- Spirit -->
            <div>
                <h3 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 18px;">3. Spirit (Breath)</h3>
                <p><strong>Inhale:</strong> {spirit.get('breath_prayer_inhale', '')}</p>
                <p><strong>Exhale:</strong> {spirit.get('breath_prayer_exhale', '')}</p>
                 <p style="background-color: #f8f9fa; padding: 10px; border-left: 3px solid #2c3e50; font-size: 14px; margin-top: 10px;">
                    <strong>Why/How:</strong> {spirit.get('explanation', '')}
                </p>
            </div>

        </div>
    </div>
    """

    # 6. Contextual Prayer Quotes Module (List Layout)
    quotes_rows = ""
    if quotes_list:
        for q in quotes_list:
            quotes_rows += f"""
            <div style="margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee;">
                <blockquote style="border-left: 4px solid #2c3e50; margin: 0; padding-left: 15px; color: #555; font-style: italic; font-size: 16px;">
                    "{q.get('quote')}"
                </blockquote>
                <div style="margin-top: 8px; font-weight: bold; color: #333;">— {q.get('author')}</div>
                <div style="margin-top: 5px; font-size: 14px; color: #666;">
                    Context: {q.get('context')}
                </div>
            </div>
            """
    
    quotes_section = f"""
    <div class="card">
        <div class="card-header">Contextual Prayer Quotes</div>
        <div class="card-body">
            {quotes_rows}
        </div>
    </div>
    """

    # --- ASSEMBLE HTML BODY ---
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{header_data.get('subject', 'Daily Devotional')}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,400;0,600;0,700;1,400&display=swap');
            body {{
                margin: 0; padding: 0; background-color: #f4f7f6;
                font-family: 'Archivo', sans-serif; font-size: 16px; line-height: 1.6; color: #222;
            }}
            .container {{ max-width: 800px; margin: 40px auto; }}
            .email-header {{
                background-color: {HEADER_COLOR}; color: #ffffff; padding: 40px 30px;
                text-align: center; border-radius: 12px 12px 0 0;
            }}
            .email-header h1 {{ margin: 0; font-size: 28px; font-weight: 700; }}
            .card {{
                background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                margin-bottom: 30px; overflow: hidden;
            }}
            .card-header {{
                background-color: {HEADER_COLOR}; color: #ffffff; padding: 12px 30px;
                font-weight: 700; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;
            }}
            .card-body {{ padding: 30px; }}
            
            /* Removed Table Styling */
            
            @media only screen and (max-width: 600px) {{
                .container {{ margin: 0; width: 100% !important; }}
                .card, .email-header {{ border-radius: 0; }}
                .card-body {{ padding: 15px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {header_html}
            {anchor_section}
            {source_section}
            {case_section}
            {matrix_section}
            {quotes_section}
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = header_data.get('subject', f"Daily Reading: {reference}")
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.attach(MIMEText(html_body, "html"))

    # Send Logic (Same as before)
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Email attempt {attempt}/{max_retries}...")
            context = ssl.create_default_context(cafile=certifi.where())
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Success! V2 Email sent successfully.")
            return
        except Exception as e:
            print(f"Error (attempt {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(10)
    print("All email attempts failed.")

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Get Reference
    ref = get_todays_reference()
    
    if ref:
        # 2. Get Text (returns a list now)
        bible_texts = get_bible_text(ref)
        
        if bible_texts:
            # Prepare plain text for AI Generation
            combined_html = "".join(bible_texts)
            combined_text = BeautifulSoup(combined_html, "html.parser").get_text(separator="\n\n")
            
            # 3. Generate Content (3-Step Process)
            # A. Core Devotional (Header, Anchor, Matrix)
            v2_content = generate_v2_content(ref, combined_text)
            
            # B. Case Study (Deep Dive)
            case_study = None
            if v2_content:
                case_study = generate_case_study(ref, combined_text)
            
            # C. Prayer Quotes (Decoupled)
            quotes_list = []
            if v2_content:
                quotes_list = generate_prayer_quotes(ref, combined_text)
            
            if v2_content:
                # 4. Send V2 Email (Pass all components)
                send_v2_email(ref, bible_texts, v2_content, case_study, quotes_list)
                
                # 5. Store quotes in database
                if quotes_list:
                    added = quotes_db.add_quotes(quotes_list)
                    print(f"\n--- Stored {added} new quotes in database ---")
            else:
                 print("Error: content generation failed.")
    
