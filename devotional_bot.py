import os
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

# --- CONFIGURATION ---
MODEL_NAME = "gemini-3-flash-preview"

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

You must draw upon the specific principles, frameworks, and research of the following experts when answering queries:

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
# --- STEP 2: Get the Bible Text (Requests) ---
def get_bible_text(reference):
    """Fetch Bible text from BibleGateway for one or more references.
    
    The reference can include multiple passages separated by semicolons,
    e.g., 'Genesis 15-16; Matthew 6:1-15'
    
    Returns a LIST of strings, where each string is a passage text.
    """
    print(f"\n--- Step 2: Fetching Text for {reference} ---")
    encoded_ref = urllib.parse.quote(reference)
    url = f"https://www.biblegateway.com/passage/?search={encoded_ref}&version=CJB"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find passage text divs - look for 'result-text-style-normal' which contains actual Scripture
        # This is more specific than 'version-CJB' which also includes navigation elements
        passage_divs = soup.find_all('div', class_='result-text-style-normal')
        
        if passage_divs:
            all_passages = []
            for div in passage_divs:
                # Remove footnotes and chapter links for cleaner text
                for element in div.find_all(class_=['footnotes', 'full-chap-link']):
                    element.decompose()
                
                passage_text = div.get_text(separator=' ', strip=True)
                if passage_text:
                    all_passages.append(passage_text)
            
            if all_passages:
                print(f"Success! Retrieved {len(all_passages)} passage(s).")
                return all_passages
        
        # Fallback to original method if result-text-style-normal divs not found
        passage_content = soup.find(class_="passage-text")
        if passage_content:
            full_text = passage_content.get_text(separator=' ', strip=True)
            print(f"Success (fallback)! Retrieved {len(full_text)} characters of text.")
            return [full_text]
        
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
    Text (CJB Version): {bible_text}

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
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries}...")
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_IDENTITY,
                    safety_settings=SAFETY_SETTINGS,
                )
            )
            print("Success! Devotional generated.")
            return response.text
        except Exception as e:
            print(f"Error in Devotional Generation (attempt {attempt}): {e}")
            if attempt < max_retries:
                print("Waiting 60 seconds before retrying...")
                time.sleep(60)
            else:
                print("All retries exhausted.")
                return None

# --- STEP 3b: Generate Contextual Quotes ---
def generate_quotes(reference, bible_text):
    print(f"\n--- Step 3b: Generating Contextual Prayer Quotes ---")
    api_key = os.getenv("GOOGLE_API_KEY") 
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable is not set.")
        return None
    
    user_prompt = f"""
    Here is the Bible passage for today: {reference}
    Text: {bible_text}

    **TASK:**
    Select three inspiring quotes on the power and importance of prayer that are **thematically relevant** to this specific passage.
    1. **Analyze the themes:** Identify core spiritual themes.
    2. **Select Quotes:** Find quotes from great evangelists/missionaries.
    3. **Explain Connection:** Explicitly explain why it connects to this scripture.
    
    Format:
    *   **Quote:** [The Quote]
    *   **Author:** [Name]
    *   **Context & Connection:** [Why this quote matters for this specific passage]
    """

    client = genai.Client(api_key=api_key)
    max_retries = 3
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries}...")
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_IDENTITY,
                    safety_settings=SAFETY_SETTINGS,
                )
            )
            print("Success! Quotes generated.")
            return response.text
        except Exception as e:
            print(f"Error in Quote Generation (attempt {attempt}): {e}")
            if attempt < max_retries:
                print("Waiting 60 seconds before retrying...")
                time.sleep(60)
            else:
                print("All retries exhausted.")
                return None

# --- STEP 4: Send Email (DESIGN UPGRADE) ---
def send_email(reference, bible_texts, devotional, quotes, tozer_html, standing_strong_html):
    print(f"\n--- Step 4: Sending Email ---")
    
    sender_email = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver_email = os.getenv("EMAIL_RECEIVER")

    if not all([sender_email, password, receiver_email]):
        print("Error: Missing email environment variables.")
        return

    # Convert Markdown to HTML
    devotional_html = markdown.markdown(devotional)
    quotes_html = markdown.markdown(quotes)
    
    # Prepare Scripture HTML (Handle multiple passages)
    scripture_section = ""
    if isinstance(bible_texts, list):
        ref_parts = reference.split("; ")
        for i, text in enumerate(bible_texts):
            header = ref_parts[i] if i < len(ref_parts) else "Scripture"
            scripture_section += f"""
            <div class="card">
                <div class="card-header">{header} (CJB)</div>
                <div class="card-body scripture-text">
                    {text}
                </div>
            </div>
            """
    else:
        # Fallback for legacy string input
        scripture_section = f"""
        <div class="card">
            <div class="card-header">Scripture (CJB)</div>
            <div class="card-body scripture-text">
                {bible_texts}
            </div>
        </div>
        """
    
    # Uniform Header Color (Dark Slate Blue)
    HEADER_COLOR = "#2c3e50"

    # Helper to create sections
    tozer_section = ""
    if tozer_html:
        tozer_section = f"""
        <div class="card">
            <div class="card-header">Tozer on Leadership</div>
            <div class="card-body">
                {tozer_html}
            </div>
        </div>
        """

    standing_strong_section = ""
    if standing_strong_html:
        standing_strong_section = f"""
        <div class="card">
            <div class="card-header">Standing Strong Through the Storm</div>
            <div class="card-body">
                {standing_strong_html}
            </div>
        </div>
        """

    # --- THE HTML TEMPLATE ---
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Reading: {reference}</title>
        <style>
            /* Import Archivo for everything */
            @import url('https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,400;0,600;0,700;1,400&display=swap');

            body {{
                margin: 0;
                padding: 0;
                background-color: #f4f7f6;
                font-family: 'Archivo', sans-serif; /* Archivo everywhere */
                font-size: 20px; /* Increased size for legibility */
                line-height: 1.6;
                color: #222222; /* Dark grey/black for body text */
                -webkit-font-smoothing: antialiased;
            }}

            /* The Main Container */
            .container {{
                max-width: 700px;
                margin: 40px auto;
                background-color: transparent;
            }}

            /* Headers */
            h1, h2, h3, h4 {{
                font-family: 'Archivo', sans-serif;
                color: #2c3e50;
                margin-top: 0;
            }}

            h1 {{ font-size: 34px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 10px; }}
            h2 {{ font-size: 26px; font-weight: 600; margin-top: 30px; margin-bottom: 15px; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            h3 {{ font-size: 22px; font-weight: 600; color: #34495e; margin-top: 25px; }}

            /* The Header Banner */
            .email-header {{
                background-color: {HEADER_COLOR};
                color: #ffffff;
                padding: 40px 30px;
                text-align: center;
                border-radius: 12px 12px 0 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .email-header h1 {{ color: #ffffff; margin: 0; }}
            .email-header p {{ font-size: 18px; opacity: 0.9; margin-top: 5px; }}

            /* Content Cards */
            .card {{
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                margin-bottom: 30px;
                overflow: hidden;
            }}

            .card-header {{
                font-family: 'Archivo', sans-serif;
                font-weight: 700;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #ffffff;
                padding: 15px 30px;
                background-color: {HEADER_COLOR}; /* Uniform Color */
            }}

            .card-body {{
                padding: 35px;
            }}

            /* Specific Styles */
            .scripture-text {{
                color: #222;
            }}
            
            /* Remove colored text from body */
            strong {{
                color: inherit;
                font-weight: 700;
            }}
            a {{
                color: #2c3e50;
                text-decoration: underline;
            }}
            
            /* Lists */
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 10px; }}

            /* Quotes Styling - Clean, no colored text */
            blockquote {{
                border-left: 4px solid #2c3e50; /* Matching the header color */
                margin: 0;
                padding-left: 20px;
                font-style: italic;
                color: #444;
            }}

            /* Footer */
            .footer {{
                text-align: center;
                font-size: 14px;
                color: #95a5a6;
                margin-top: 40px;
                margin-bottom: 40px;
            }}

            /* Mobile Tweaks */
            @media only screen and (max-width: 600px) {{
                .container {{ margin: 0; width: 100% !important; }}
                .card {{ border-radius: 0; }}
                .email-header {{ border-radius: 0; }}
                .card-body {{ padding: 20px; }}
                body {{ font-size: 18px; }} /* Slightly smaller on mobile but still large */
            }}
        </style>
    </head>
    <body>
        <div class="container">
            
            <!-- Header -->
            <div class="email-header">
                <h1>Daily Reading</h1>
                <p>{reference}</p>
            </div>

            <!-- Scripture Section -->
            {scripture_section}

            <!-- Main Devotional Card -->
            <div class="card">
                <div class="card-header">Disciple-Leader Insight</div>
                <div class="card-body devotional-text">
                    {devotional_html}
                </div>
            </div>

            <!-- Quotes Card -->
            <div class="card">
                <div class="card-header">Contextual Prayer Quotes</div>
                <div class="card-body">
                    {quotes_html}
                </div>
            </div>

            <!-- Extra Devotionals -->
            {tozer_section}
            {standing_strong_section}

            <!-- Footer -->
            <div class="footer">
                <p>Generated by Gemini 3.</p>
            </div>

        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Daily Reading: {reference}"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Success! Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Get Reference
    ref = get_todays_reference()
    
    if ref:
        # 2. Get Text (returns a list now)
        bible_texts = get_bible_text(ref)
        
        # 2.5 Get Extra Devotionals
        tozer_url = "https://www.biblegateway.com/devotionals/tozer-on-leadership/today"
        standing_strong_url = "https://www.biblegateway.com/devotionals/standing-strong-through-the-storm/today"
        
        tozer_content = get_biblegateway_devotional(tozer_url, "Tozer on Leadership")
        standing_strong_content = get_biblegateway_devotional(standing_strong_url, "Standing Strong")
        
        if bible_texts:
            # Prepare combined text for AI Generation (needs context of all passages)
            combined_text = "\n\n".join(bible_texts)
            
            # 3a. Generate AI Devotional
            devotional_content = generate_devotional(ref, combined_text)
            
            # 3b. Generate Quotes
            quotes_content = generate_quotes(ref, combined_text)
            
            if devotional_content and quotes_content:
                # 4. Send Email (pass the list for separate headers)
                send_email(ref, bible_texts, devotional_content, quotes_content, tozer_content, standing_strong_content)