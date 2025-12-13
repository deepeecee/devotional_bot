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
# Using the requested model version
MODEL_NAME = "gemini-2.5-flash"

# Permissive Safety Settings (Critical for Bible content which can trigger violence filters)
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
3.  Don't output your "Stream of Consciousness" logic or the "Polya Heuristic" steps explicitly (Understand, Devise, Carry Out, Look Back). These should be internal thoughts only.
4.  Cite experts from the Knowledge Base where relevant.
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

# --- STEP 3a: Generate Devotional ---
def generate_devotional(reference, bible_text):
    print(f"\n--- Step 3a: Generating Devotional for {reference} ---")
    api_key = os.getenv("GOOGLE_API_KEY") 
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
        print(f"Success in Devotional Generation!")
        return response.text
    except Exception as e:
        print(f"Error in Devotional Generation: {e}")
        return None

# --- STEP 3b: Generate Contextual Quotes ---
def generate_quotes(reference, bible_text):
    print(f"\n--- Step 3b: Generating Contextual Prayer Quotes for {reference} ---")
    api_key = os.getenv("GOOGLE_API_KEY") 
    print(api_key)
    if not api_key: return None
    genai.configure(api_key=api_key)
    
    user_prompt = f"""
    Here is the Bible passage for today: {reference}
    Text: {bible_text}

    **TASK:**
    Select three inspiring quotes on the power and importance of prayer that are **thematically relevant** to this specific passage.
    1. **Analyze the themes:** Identify core spiritual themes (suffering, joy, obedience, etc.).
    2. **Select Quotes:** Find quotes from great evangelists/missionaries that speak to these themes.
    3. **Explain Connection:** Explicitly explain why it connects to this scripture.
    
    Format:
    *   **Quote:** [The Quote]
    *   **Author:** [Name]
    *   **Context & Connection:** [Why this quote matters for this specific passage]
    """

    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_IDENTITY)
        response = model.generate_content(user_prompt, safety_settings=SAFETY_SETTINGS)
        print(f"Success in Devotional Generation!")
        return response.text
    except Exception as e:
        print(f"Error in Quote Generation: {e}")
        return None

# --- STEP 4: Send Email ---
def send_email(reference, bible_text, devotional, quotes):
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
    
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h1 style="color: #2c3e50;">Daily Reading: {reference}</h1>
        
        <div style="background-color: #f9f9f9; padding: 15px; border-left: 5px solid #3498db; margin-bottom: 20px;">
            <h3 style="margin-top: 0;">Scripture (CJB)</h3>
            <p style="white-space: pre-wrap;">{bible_text}</p>
        </div>

        <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">

        <h2 style="color: #2c3e50;">Devotional</h2>
        {devotional_html}

        <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">

        <h2 style="color: #2c3e50;">Contextual Prayer Quotes</h2>
        <div style="background-color: #e8f6f3; padding: 15px; border-radius: 5px;">
            {quotes_html}
        </div>
        
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
        # SSL Context with Certifi (Fixes the SSL Certificate Verify Failed error)
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
        
        if bible_text:
            # 3a. Generate Devotional
            devotional_content = generate_devotional(ref, bible_text)
            
            # 3b. Generate Quotes
            quotes_content = generate_quotes(ref, bible_text)
            
            if devotional_content and quotes_content:
                print("Success! Devotional and Quotes generated successfully.")
                # 4. Send Email
                send_email(ref, bible_text, devotional_content, quotes_content)