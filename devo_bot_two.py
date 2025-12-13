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

# --- STEP 4: Send Email ---
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
    
    # Handle cases where extra devotionals might be None
    tozer_section = f"""
    <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
    <h2 style="color: #8e44ad;">Tozer on Leadership</h2>
    <div style="background-color: #f4ecf7; padding: 15px; border-radius: 5px;">
        {tozer_html}
    </div>
    """ if tozer_html else ""

    standing_strong_section = f"""
    <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
    <h2 style="color: #c0392b;">Standing Strong Through the Storm</h2>
    <div style="background-color: #fdedec; padding: 15px; border-radius: 5px;">
        {standing_strong_html}
    </div>
    """ if standing_strong_html else ""
    
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h1 style="color: #2c3e50;">Daily Reading: {reference}</h1>
        
        <div style="background-color: #f9f9f9; padding: 15px; border-left: 5px solid #3498db; margin-bottom: 20px;">
            <h3 style="margin-top: 0;">Scripture (CJB)</h3>
            <p style="white-space: pre-wrap;">{bible_text}</p>
        </div>

        <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">

        <h2 style="color: #2c3e50;">Disciple-Leader Insight</h2>
        {devotional_html}

        <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">

        <h2 style="color: #27ae60;">Contextual Prayer Quotes</h2>
        <div style="background-color: #e8f6f3; padding: 15px; border-radius: 5px;">
            {quotes_html}
        </div>

        {tozer_section}

        {standing_strong_section}
        
        <p style="font-size: 12px; color: #888; margin-top: 40px;">
            Generated by your Disciple-Leader AI Assistant.
        </p>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Daily Reading & Devotional: {reference}"
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