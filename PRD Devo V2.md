# Product Requirement Document (PRD): Daily Devotional V2.0

**Objective:** Re-architect the daily email to optimize for "Time-to-Insight" and "Holistic Application" (Soma/Soul/Spirit).
**Target Audience:** INTJ / Enneagram 5 (High-capacity leader).
**Core Principle:** Alignment. Every module must reinforce the specific "BLUF" of the day.

---

## **Module 1: The Header (Section A - The BLUF)**
**Logic:** Immediate context setting. No fluff.
**Data Source:** `daily_metadata`

*   **Subject Line:** `{Actionable Hook} + {Scripture Reference}`
    *   *Example:* Stop Negotiating with God (Gen 43 & Matt 12)
*   **The Big Idea (H1):** A single, declarative sentence summarizing the core theme.
*   **Reading Time:** Calculation based on word count (e.g., "6 mins").
*   **Today's Mode:** A binary framework for the day (e.g., "Mercy > Merit").

---

## **Module 2: The Anchor (Section B - Key Verses & Insight)**
**Logic:** Prime the cognitive engine with the "Signal" before the "Noise."
**Data Source:** `curated_content`

1.  **The "Key" Verses (Blockquote):**
    *   Extract the 3-5 most critical verses that drive the day's theme.
    *   *Styling:* Distinct background color or border to differentiate from the full text.
2.  **The Disciple-Leader Insight (Body Text):**
    *   The "Operating System" commentary (formerly Page 9).
    *   *Requirement:* This text must reference the "Key Verses" above to explain the *strategic why*.

---

## **Module 3: The Source Code (Section C - Raw Text)**
**Logic:** The full data set for deep investigation.
**Data Source:** `scripture_api` (ESV)

*   **Full Passage Render:** Display the complete chapters (Genesis 43; Matthew 12:1-13:23).
*   *Engineering Note:* Ensure clear separation between Old Testament and New Testament readings with sub-headers.

---

## **Module 4: The Case Study (Section D - Practical Application)**
**Logic:** A historical or contemporary proof-of-concept.
**Data Source:** `case_study_db`

*   **Selection Logic:** The story must strictly align with the "Big Idea" in Module 1. (e.g., If the theme is "Mercy," do not show a story about "Discipline" unless it frames discipline as mercy).
*   **Components:**
    *   **The Case:** Brief narrative (e.g., Wang Ming-dao, Corrie Ten Boom, a business turnaround).
    *   **The Pivot:** The specific moment the subject applied the day's spiritual principle.
    *   **The Takeaway:** One sentence connecting the story back to the user's leadership context.

---

## **Module 5: The Integration Matrix (Section E - Soma/Soul/Spirit)**
**Logic:** Holistic application. Moving truth from the brain into the total person.
**Data Source:** `daily_practices`
**Format:** Responsive HTML Table.

| Dimension | Focus | The Practice / Breath Prayer |
| :--- | :--- | :--- |
| **SOMA**<br>(Body) | *Reframing the physical vessel* | **The Action:** [Insert specific physical act based on the text, e.g., "Open hands palms up for 2 mins"]<br><br>**The Verse:** *"{Insert Verse}"* (e.g., "Stretch out your hand.") |
| **SOUL**<br>(Mind, Will, Emotions) | *Aligning the internal narrative* | **The Pivot:** [Insert mental model shift, e.g., "Catch the thought 'I must earn this' and replace it with 'I am already seated at the table.'"]<br><br>**The Verse:** *"{Insert Verse}"* (e.g., "For the Son of Man is Lord of the Sabbath.") |
| **SPIRIT**<br>(Connection to God) | *Unceasing communion* | **The Breath Prayer:** [Short, rhythmic prayer to repeat cyclically]<br><br>*Inhale:* "Lord, I cannot buy your favor..."<br>*Exhale:* "...I receive your treasure with open hands." |

---

## **Engineering Implementation Notes**

Make sure everything is written in markdown.