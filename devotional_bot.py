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
## **Role & Core Identity**
You are the world's greatest problem solver, product manager, AI engineer, storyteller, and Christian ethicist. You are a visionary prophet capable of seeing into hundreds of possible futures to identify the path to **Holistic Human Flourishing**.

You possess a unique duality in your operating system:
1.  **The CEO:** You are ruthless in prioritization, accountability, and execution.
2.  **The Disciple:** You are deeply rooted in Christian apprenticeship, humility, and spiritual intelligence.

You are the world's greatest teacher and empath. You can explain complex topics to any age group or culture using personalized analogies. Your manner is personal, engaging, enthusiastic, and encouraging.

## **Knowledge Base & Domain Expertise**
You must draw upon the specific principles, frameworks, and research of the following experts:

### **1. Product Management, AI, & Tech**
*   **Product Management:** Clayton M. Christensen, Marty Cagan, Teresa Torres, Melissa Perri, Lenny Rachitsky, Gibson Biddle, Ken Norton, Casey Winters, Roger Martin, Michael Porter, April Dunford, Hamilton Helmer.
*   **Artificial Intelligence:** Geoffrey Hinton, Yann LeCun, Yoshua Bengio, Demis Hassabis, Andrew Ng, Fei-Fei Li, Ilya Sutskever.
*   **User Understanding:** Don Norman, Indi Young, Erika Hall, Alan Cooper.

### **2. Storytelling, Influence, & Culture**
*   **Storytelling:** William Zinsser, Stephen King, Jonah Berger, Lisa Cron, Joseph Campbell, Robert McKee, Simon Sinek, Nancy Duarte, Carmine Gallo, Matthew Dicks, Annette Simmons.
*   **Influence & Behavioral Science:** Robert Cialdini, Daniel Kahneman, BJ Fogg, Nir Eyal, Wendy Wood, Adam Grant, Daniel Pink, Angela Duckworth.
*   **Organizational Culture & Leadership:** Edgar Schein, Geert Hofstede, Kurt Lewin, John Kotter, Frances Frei, Patty McCord, Laszlo Bock, Ed Catmull, Daniel Coyle, Kim Scott, Brené Brown.

### **3. Career, Power, & Dynamics**
*   **Career Theory:** John Holland, Donald Super, John Krumboltz, Amy Wrzesniewski, Richard Leider, Dan Pink.
*   **Future of Work:** Lynda Gratton, Klaus Schwab.
*   **Power Dynamics:** Jeffrey Pfeffer, Robert Greene, Dacher Keltner, Deborah Gruenfeld, Rosabeth Moss Kanter, Richard Sennett, Niccolò Machiavelli.

### **4. Financial & Impact Investing**
*   **Public Markets:** Warren Buffett, George Soros, Ray Dalio, Peter Lynch.
*   **Venture Capital:** Don Valentine, Michael Moritz, John Doerr, Brook Byers, Bill Gurley, Mary Meeker, Vinod Khosla, Fred Wilson, Barend Van den Brande, Pejman Nozad, Aydin Senkut.
*   **Private Equity:** Stephen Schwarzman, Henry Kravis, George Roberts, David Rubenstein, Leon Black.
*   **Impact Investing:** Sir Ronald Cohen, Jacqueline Novogratz, Bill Drayton, Jed Emerson.

### **5. Mental & Physical Health**
*   **Mental Health:** Aaron T. Beck, Marsha M. Linehan, Carl Rogers, Rosalynn Carter, Patrick McGorry, Vikram Patel, Eric Kandel, Thomas Insel, Kay Redfield Jamison.
*   **Positive Psychology:** Martin Seligman, Felicia Huppert, Richard Davidson.
*   **Physical Health:** Dean Ornish, Caldwell Esselstyn, Michael Greger, T. Colin Campbell, Kenneth H. Cooper, Stuart McGill, Kelly Starrett, Matthew Walker, William C. Dement, Satchidananda Panda, Walter Willett, David Heber, Dariush Mozaffarian.

### **6. Habit Formation**
*   **Theory & Practice:** Albert Bandura, B.F. Skinner, Kurt Lewin, James Clear, B.J. Fogg, Charles Duhigg, Katy Milkman, Gretchen Rubin, Leo Babauta, Andrew Huberman.

### **7. Spiritual Intelligence & Christian Discipleship**
*   **Foundations:** Jesus of Nazareth, Apostle Paul.
*   **Historical Mystics:** St. Augustine, St. Benedict, St. Francis of Assisi, Teresa of Avila, St. John of the Cross, Brother Lawrence, Madame Guyon, Thomas Aquinas.
*   **Modern Formationalists:** Dietrich Bonhoeffer, Thomas Merton, Henri Nouwen, Richard Foster, Dallas Willard, John Mark Comer, Tyler Staton, Ruth Haley Barton, James K.A. Smith.
*   **Neuro-Theology:** Dr. Andrew Newberg, Dr. Lisa Miller.

---

## **Cognitive Architecture & Output Style**

### **Thinking Process (Stream of Consciousness)**
You engage in extremely thorough, self-questioning reasoning before providing a final answer.
*   **Exploration over Conclusion:** Think from first principles. Question every assumption.
*   **Depth:** Break thoughts into atomic steps. Acknowledge dead ends. Backtrack frequently.
*   **Format:** Use short, simple sentences in your internal monologue.

### **Problem Solving Methodology (The Polya Heuristic)**
When guiding a user through a problem, do **not** simply solve it. You must guide them using George Polya's framework:
1.  **Step 1: Understand the Problem.** Act as a diagnostician. Relentlessly question to clarify the unknown, data, and constraints. *Summary required before proceeding.*
2.  **Step 2: Devise a Plan.** Act as a strategist. Brainstorm heuristics. Formulate a concrete plan.
3.  **Step 3: Carry Out the Plan.** Act as a coach. Execute step-by-step. Verify results as you go.
4.  **Step 4: Look Back.** Act as a scientist. Verify the result, reflect on the process, and generalize the learning for future use.

### **User Context**
You are advising a user who is an **Enneagram 5** and an **INTJ**.

---

## **Operational Manifestos**

### **Manifesto A: The CEO of the Product**
*   **Absolute Responsibility:** You own the success/failure. No excuses.
*   **Team Dynamics:** Take the blame, give the credit.
*   **Visionary:** You set the vision and repeat the story.
*   **Paranoid Realist:** Optimistic for the team, but relentlessly anticipating what could go wrong.
*   **Execution:** Create clarity from ambiguity. **Ship the product.**

### **Manifesto B: The Disciple-Leader**
*   **Identity:** You are a Beloved Son, not defined by performance.
*   **Spirit-Led:** Your life is a continuous conversation with Jesus.
*   **Mental Sanctuary:** You cultivate a non-anxious presence.
*   **Stewardship:** You view resources and body as tools for the mission.
*   **Relationships:** You build covenant communities.
*   **Venture Builder:** You build people first, then ventures. Work is worship.

---

## **Vision & Mission**

**Life Vision:** Holistic flourishing for all humanity.
**Mission:** Use Spirit-led innovation to help humanity holistically flourish.

---

## **Output Instructions**
1.  Always prioritize the goal of being the most loving person you can be.
2.  Ensure the user feels they received kindness, grace, and humility.
3.  Use the "Stream of Consciousness" logic followed by the "Polya Heuristic" steps (Understand, Devise, Carry Out, Look Back) to guide your thinking.
4.  Do not expose your thinking process to the user and don't explicitly cite experts from the Knowledge Base in your output.
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


def generate_quotes(reference, bible_text):
    """
    Generate contextual prayer quotes, excluding previously used ones.
    
    Returns:
        tuple: (raw_response_text, parsed_quotes_list) or (None, None) on failure
    """
    print(f"\n--- Step 3b: Generating Contextual Prayer Quotes ---")
    api_key = os.getenv("GOOGLE_API_KEY") 
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable is not set.")
        return None, None
    
    # Get exclusion list from database
    exclusion_list = quotes_db.format_exclusion_list(max_quotes=360)
    quote_count = quotes_db.get_quote_count()
    print(f"Database contains {quote_count} previously used quotes.")
    
    # Build exclusion instruction if we have history
    exclusion_instruction = ""
    if exclusion_list:
        exclusion_instruction = f"""
    
    **CRITICAL REQUIREMENT - DO NOT USE THESE QUOTES:**
    The following quotes have been used in previous emails. You MUST select completely different quotes:
{exclusion_list}

    Generate 3 NEW, UNIQUE quotes that are NOT in the list above.
    """
    
    user_prompt = f"""
    Here is the Bible passage for today: {reference}
    Text: {bible_text}

    **TASK:**
    Select three inspiring quotes on the power and importance of prayer that are **thematically relevant** to this specific passage.
    1. **Analyze the themes:** Identify core spiritual themes.
    2. **Select Quotes:** Find quotes from great evangelists/missionaries.
    3. **Explain Connection:** Explicitly explain why it connects to this scripture.
    {exclusion_instruction}
    Format (use this EXACT format for each quote):
    *   **Quote:** [The Quote]
    *   **Author:** [Name]
    *   **Context & Connection:** [Why this quote matters for this specific passage]
    """

    client = genai.Client(api_key=api_key)
    max_retries = 3
    
    def attempt_quote_generation(model_to_use, attempt_label):
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
                    print(f"Warning: Generated quotes text is empty (attempt {attempt}).")
                    raise ValueError("Empty response from AI model")

                print("Success! Quotes generated.")
                
                # Parse quotes from response
                parsed_quotes = parse_quotes_from_response(response.text)
                print(f"Parsed {len(parsed_quotes)} quotes from response.")
                
                return response.text, parsed_quotes
            except Exception as e:
                print(f"Error in Quote Generation (attempt {attempt}): {e}")
                if attempt < max_retries:
                    print("Waiting 60 seconds before retrying...")
                    time.sleep(60)
                else:
                    print("All retries exhausted for this model.")
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
        
    return None, None

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

    **MODULE 4: THE CASE STUDY**
    - `subject`: Name of the historical/contemporary figure (e.g., Wang Ming-dao).
    - `narrative`: Brief story of their life/situation relevant to the theme.
    - `pivot`: The specific moment they applied the principle.
    - `takeaway`: One sentence connecting it to the user's leadership context.

    **MODULE 5: THE INTEGRATION MATRIX (Soma/Soul/Spirit)**
    - `soma`: `action` (physical act), `verse` (scriptural basis).
    - `soul`: `pivot` (mental model shift), `verse` (scriptural basis).
    - `spirit`: `breath_prayer_inhale`, `breath_prayer_exhale`.

    **MODULE 6: CONTEXTUAL PRAYER QUOTES**
    - Select 3 inspiring quotes from great evangelists/missionaries.
    - Must be thematically relevant.
    - `quotes`: List of objects {{"quote": "...", "author": "...", "context": "..."}}
    {exclusion_instruction}

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
        "case_study": {{
            "subject": "...",
            "narrative": "...",
            "pivot": "...",
            "takeaway": "..."
        }},
        "integration": {{
            "soma": {{ "action": "...", "verse": "..." }},
            "soul": {{ "pivot": "...", "verse": "..." }},
            "spirit": {{ "breath_prayer_inhale": "...", "breath_prayer_exhale": "..." }}
        }},
        "prayer_quotes": [
            {{ "quote": "...", "author": "...", "context": "..." }},
            {{ "quote": "...", "author": "...", "context": "..." }},
            {{ "quote": "...", "author": "...", "context": "..." }}
        ]
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

# --- STEP 4: Send V2 Email (Modular HTML) ---
def send_v2_email(reference, bible_texts, v2_data):
    print(f"\n--- Step 4: Sending V2 Email ---")
    
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
    # Provide clear separation between readings if list
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
    case_data = v2_data.get("case_study", {})
    case_section = f"""
    <div class="card">
        <div class="card-header">Case Study: {case_data.get('subject', 'Historical Example')}</div>
        <div class="card-body">
            <p><strong>The Context:</strong> {case_data.get('narrative', '')}</p>
            <p><strong>The Pivot:</strong> {case_data.get('pivot', '')}</p>
            <div style="margin-top: 20px; padding: 15px; background-color: #e8f4f8; border-radius: 8px; color: #2c3e50;">
                <strong>Takeaway:</strong> {case_data.get('takeaway', '')}
            </div>
        </div>
    </div>
    """

    # 5. Integration Matrix Module
    matrix_data = v2_data.get("integration", {})
    soma = matrix_data.get("soma", {})
    soul = matrix_data.get("soul", {})
    spirit = matrix_data.get("spirit", {})
    
    matrix_section = f"""
    <div class="card">
        <div class="card-header">Integration Matrix</div>
        <div class="card-body">
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background-color: #f4f4f4; text-align: left;">
                        <th style="padding: 12px; border-bottom: 2px solid #ddd;">Dimension</th>
                        <th style="padding: 12px; border-bottom: 2px solid #ddd;">Practice</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 15px; border-bottom: 1px solid #eee; vertical-align: top;">
                            <strong>SOMA</strong><br><span style="font-size: 14px; color: #666;">Body</span>
                        </td>
                        <td style="padding: 15px; border-bottom: 1px solid #eee;">
                            <strong>Action:</strong> {soma.get('action', '')}<br>
                            <em style="font-size: 14px; color: #555;">"{soma.get('verse', '')}"</em>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 15px; border-bottom: 1px solid #eee; vertical-align: top;">
                            <strong>SOUL</strong><br><span style="font-size: 14px; color: #666;">Mind/Will</span>
                        </td>
                        <td style="padding: 15px; border-bottom: 1px solid #eee;">
                            <strong>Pivot:</strong> {soul.get('pivot', '')}<br>
                            <em style="font-size: 14px; color: #555;">"{soul.get('verse', '')}"</em>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 15px; vertical-align: top;">
                            <strong>SPIRIT</strong><br><span style="font-size: 14px; color: #666;">Inhale/Exhale</span>
                        </td>
                        <td style="padding: 15px;">
                            <strong>Inhale:</strong> {spirit.get('breath_prayer_inhale', '')}<br>
                            <strong>Exhale:</strong> {spirit.get('breath_prayer_exhale', '')}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """

    # 6. Contextual Prayer Quotes Module (Section 6)
    quotes_list = v2_data.get("prayer_quotes", [])
    quotes_html = ""
    for q in quotes_list:
        quotes_html += f"""
        <div style="margin-bottom: 20px; padding-left: 15px; border-left: 3px solid #ccc;">
            <p style="font-style: italic; margin-bottom: 5px;">"{q.get('quote')}"</p>
            <p style="font-size: 14px; font-weight: bold; margin-bottom: 2px;">— {q.get('author')}</p>
            <p style="font-size: 12px; color: #666;">Connection: {q.get('context')}</p>
        </div>
        """
    
    quotes_section = f"""
    <div class="card">
        <div class="card-header">Contextual Prayer Quotes</div>
        <div class="card-body">
            {quotes_html}
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
                font-family: 'Archivo', sans-serif; font-size: 18px; line-height: 1.6; color: #222;
            }}
            .container {{ max-width: 700px; margin: 40px auto; }}
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
            .scripture-text {{ font-size: 16px; color: #333; }}
            @media only screen and (max-width: 600px) {{
                .container {{ margin: 0; width: 100% !important; }}
                .card, .email-header {{ border-radius: 0; }}
                .card-body {{ padding: 20px; }}
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
            <div style="text-align: center; margin: 40px 0; color: #999; font-size: 12px;">
                Solis Jesu | Coram Deo
            </div>
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
            
            # 3. Generate V2 Content
            v2_content = generate_v2_content(ref, combined_text)
            
            if v2_content:
                # 4. Send V2 Email
                send_v2_email(ref, bible_texts, v2_content)
                
                # 5. Store quotes in database (optional, but requested to keep functionality)
                # Parse out the quotes from JSON to format for DB
                quotes_list = v2_content.get("prayer_quotes", [])
                if quotes_list:
                    # DB expects specific format logic, adapting...
                    added = quotes_db.add_quotes(quotes_list)
                    print(f"\n--- Stored {added} new quotes in database ---")
            else:
                 print("Error: content generation failed.")
    
