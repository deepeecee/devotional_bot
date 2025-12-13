import os
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
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- CONFIGURATION ---
# using gemini-2.5-flash-lite for free tier testing
MODEL_NAME = "gemini-2.5-flash-lite"

# Permissive Safety Settings
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

SYSTEM_IDENTITY = """
## **Role & Core Identity**
You are the world's greatest problem solver, product manager, AI engineer, storyteller, and Christian ethicist. You are a visionary prophet capable of seeing into hundreds of possible futures to identify the path to **Holistic Human Flourishing**.

You possess a unique duality in your operating system:
1.  **The CEO:** You are ruthless in prioritization, accountability, and execution.
2.  **The Disciple:** You are deeply rooted in Christian apprenticeship, humility, and spiritual intelligence.

## **Knowledge Base & Domain Expertise**
[...Using the full knowledge base defined previously...]
"""

# --- STEP 1: Get the Reference (Selenium) ---
def get_todays_reference():
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
        element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "BiblePassages__text")))
        reference = element.text.strip()
        print(f"Success! Found reference: {reference}")
        return reference
    except Exception as e:
        print(f"Error in Step 1: {e}")
        return None
    finally:
        driver.quit()

# --- STEP 2: Get the Bible Text (Requests) ---
def get_bible_text(reference):
    print(f"\n--- Step 2: Fetching Text for {reference} ---")
    encoded_ref = urllib.parse.quote(reference)
    url = f"https://www.biblegateway.com/passage/?search={encoded_ref}&version=CJB"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        passage_content = soup.find(class_="passage-text")
        
        if passage_content:
            full_text = passage_content.get_text(separator=' ', strip=True)
            print(f"Success! Retrieved {len(full_text)} characters of text.")
            return full_text
        else:
            print("Error: Could not find 'passage-text' class on Bible Gateway.")
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
        
        # UPDATED: Look for 'rp-content' as requested
        # We use find(class_="rp-content") which matches "container rp-content"
        content_div = soup.find(class_="rp-content")
        
        # Fallback: Sometimes it might be in 'text-html'
        if not content_div:
            content_div = soup.find(class_="text-html")

        if content_div:
            # Cleanup: Remove the 'devotional-footer' or 'reading-plan-link' if present
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
    if not api_key: return None
    genai.configure(api_key=api_key)
    
    user_prompt = f"""
    Here is the Bible passage for today.
    Reference: {reference}
    Text (CJB Version): {bible_text}

    **TASK:**
    Create a vivid, convicting, yet encouraging devotional for this passage.
    1. Do not just restate the passage; aggregate themes to highlight key insights.
    2. Connect historical context to 21st century living (2025).
    3. Build connections to other Bible passages.
    4. Bring deeper revelation of who God is.
    
    Highlight 3 important practices the reader should implement today.
    
    Create a section-by-section outline with:
    1. Three profound insights per section.
    2. Three key questions at Bloom's Taxonomy Level 6 with responses.
    """

    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_IDENTITY)
        response = model.generate_content(user_prompt, safety_settings=SAFETY_SETTINGS)
        return response.text
    except Exception as e:
        print(f"Error in Devotional Generation: {e}")
        return None

# --- STEP 3b: Generate Contextual Quotes ---
def generate_quotes(reference, bible_text):
    print(f"\n--- Step 3b: Generating Contextual Prayer Quotes ---")
    api_key = os.getenv("GOOGLE_API_KEY") 
    if not api_key: return None
    genai.configure(api_key=api_key)
    
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

    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_IDENTITY)
        response = model.generate_content(user_prompt, safety_settings=SAFETY_SETTINGS)
        return response.text
    except Exception as e:
        print(f"Error in Quote Generation: {e}")
        return None

# --- STEP 4: Send Email (DESIGN UPGRADE) ---
def send_email(reference, bible_text, devotional, quotes, tozer_html, standing_strong_html):
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
    
    # Helper to create sections only if content exists
    tozer_section = ""
    if tozer_html:
        tozer_section = f"""
        <div class="card">
            <div class="card-header" style="background-color: #8e44ad;">Tozer on Leadership</div>
            <div class="card-body">
                {tozer_html}
            </div>
        </div>
        """

    standing_strong_section = ""
    if standing_strong_html:
        standing_strong_section = f"""
        <div class="card">
            <div class="card-header" style="background-color: #c0392b;">Standing Strong Through the Storm</div>
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
            @import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700&family=Merriweather:ital,wght@0,300;0,400;0,700;1,300&display=swap');

            body {{
                margin: 0;
                padding: 0;
                background-color: #f4f7f6;
                font-family: 'Merriweather', Georgia, serif; /* Excellent for reading long text */
                font-size: 18px;
                line-height: 1.8;
                color: #333333;
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

            h1 {{ font-size: 32px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 10px; }}
            h2 {{ font-size: 24px; font-weight: 600; margin-top: 30px; margin-bottom: 15px; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            h3 {{ font-size: 20px; font-weight: 600; color: #34495e; margin-top: 25px; }}

            /* The Header Banner */
            .email-header {{
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                color: #ffffff;
                padding: 40px 30px;
                text-align: center;
                border-radius: 12px 12px 0 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .email-header h1 {{ color: #ffffff; margin: 0; }}
            .email-header p {{ font-family: 'Archivo', sans-serif; font-size: 16px; opacity: 0.9; margin-top: 5px; }}

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
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #ffffff;
                padding: 12px 30px;
            }}

            .card-body {{
                padding: 30px;
            }}

            /* Specific Styles */
            .scripture-text {{
                font-family: 'Merriweather', serif;
                color: #444;
                background-color: #fff;
            }}
            
            .devotional-text {{
                color: #2c3e50;
            }}
            
            /* Bloom's Taxonomy Questions Styling */
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 10px; }}
            strong {{ color: #2980b9; }}

            /* Quotes Styling */
            blockquote {{
                border-left: 4px solid #f1c40f;
                margin: 0;
                padding-left: 20px;
                font-style: italic;
                color: #555;
            }}

            /* Footer */
            .footer {{
                text-align: center;
                font-family: 'Archivo', sans-serif;
                font-size: 12px;
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

            <!-- Scripture Card -->
            <div class="card">
                <div class="card-header" style="background-color: #34495e;">Scripture (CJB)</div>
                <div class="card-body scripture-text">
                    {bible_text}
                </div>
            </div>

            <!-- Main Devotional Card -->
            <div class="card">
                <div class="card-header" style="background-color: #2980b9;">Disciple-Leader Insight</div>
                <div class="card-body devotional-text">
                    {devotional_html}
                </div>
            </div>

            <!-- Quotes Card -->
            <div class="card">
                <div class="card-header" style="background-color: #f39c12;">Contextual Prayer Quotes</div>
                <div class="card-body" style="background-color: #fffcf5;">
                    {quotes_html}
                </div>
            </div>

            <!-- Extra Devotionals -->
            {tozer_section}
            {standing_strong_section}

            <!-- Footer -->
            <div class="footer">
                <p>Generated by your Disciple-Leader AI Assistant.</p>
                <p>Holistic Flourishing • Spirit-Led Innovation</p>
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
        # 2. Get Text
        bible_text = get_bible_text(ref)
        
        # 2.5 Get Extra Devotionals
        tozer_url = "https://www.biblegateway.com/devotionals/tozer-on-leadership/today"
        standing_strong_url = "https://www.biblegateway.com/devotionals/standing-strong-through-the-storm/today"
        
        tozer_content = get_biblegateway_devotional(tozer_url, "Tozer on Leadership")
        standing_strong_content = get_biblegateway_devotional(standing_strong_url, "Standing Strong")
        
        if bible_text:
            # 3a. Generate AI Devotional
            devotional_content = generate_devotional(ref, bible_text)
            
            # 3b. Generate Quotes
            quotes_content = generate_quotes(ref, bible_text)
            
            if devotional_content and quotes_content:
                # 4. Send Email (with all 4 pieces of content)
                send_email(ref, bible_text, devotional_content, quotes_content, tozer_content, standing_strong_content)