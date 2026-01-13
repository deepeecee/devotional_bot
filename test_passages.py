#!/usr/bin/env python3
"""
Test script for devotional_bot passage extraction.
Tests Steps 1 and 2 without generating devotionals or sending emails.
"""

import urllib.parse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def test_get_references():
    """Test extracting all Bible passage references from wearechurchreading.com."""
    print("=" * 60)
    print("STEP 1: Testing Reference Extraction")
    print("=" * 60)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://www.wearechurchreading.com/"
        print(f"Fetching: {url}")
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        
        # Wait for at least one passage element to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "BiblePassages__text")))
        
        # Find ALL passage elements
        elements = driver.find_elements(By.CLASS_NAME, "BiblePassages__text")
        print(f"\nFound {len(elements)} BiblePassages__text elements:")
        
        references = []
        for i, el in enumerate(elements):
            text = el.text.strip()
            if text:
                print(f"  {i+1}. '{text}'")
                references.append(text)
        
        if references:
            combined = "; ".join(references)
            print(f"\nCombined reference string: '{combined}'")
            return combined
        else:
            print("ERROR: No references found!")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        return None
    finally:
        driver.quit()


def test_get_bible_text(reference):
    """Test fetching Bible text from BibleGateway for multiple references."""
    print("\n" + "=" * 60)
    print("STEP 2: Testing BibleGateway Fetch")
    print("=" * 60)
    
    encoded_ref = urllib.parse.quote(reference)
    url = f"https://www.biblegateway.com/passage/?search={encoded_ref}&version=CJB"
    print(f"URL: {url}\n")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find passage text divs with class 'result-text-style-normal'
        passage_divs = soup.find_all('div', class_='result-text-style-normal')
        print(f"Found {len(passage_divs)} result-text-style-normal div(s)")
        
        if passage_divs:
            all_passages = []
            for i, div in enumerate(passage_divs):
                # Remove footnotes and chapter links
                for element in div.find_all(class_=['footnotes', 'full-chap-link']):
                    element.decompose()
                
                passage_text = div.get_text(separator=' ', strip=True)
                if passage_text:
                    # Show preview of each passage
                    preview = passage_text[:200] + "..." if len(passage_text) > 200 else passage_text
                    print(f"\nPassage {i+1} preview ({len(passage_text)} chars):")
                    print(f"  {preview}")
                    all_passages.append(passage_text)
            
            if all_passages:
                full_text = "\n\n---\n\n".join(all_passages)
                print(f"\n✓ SUCCESS: Retrieved {len(all_passages)} passage(s), {len(full_text)} total characters")
                return full_text
        
        # Fallback
        passage_content = soup.find(class_="passage-text")
        if passage_content:
            full_text = passage_content.get_text(separator=' ', strip=True)
            print(f"\n✓ SUCCESS (fallback): Retrieved {len(full_text)} characters")
            return full_text
        
        print("ERROR: Could not find passage content")
        return None
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DEVOTIONAL BOT - PASSAGE EXTRACTION TEST")
    print("=" * 60 + "\n")
    
    # Step 1: Get references
    ref = test_get_references()
    
    if ref:
        # Step 2: Get Bible text
        text = test_get_bible_text(ref)
        
        if text:
            print("\n" + "=" * 60)
            print("TEST RESULT: ✓ PASSED")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("TEST RESULT: ✗ FAILED (Step 2)")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("TEST RESULT: ✗ FAILED (Step 1)")
        print("=" * 60)
