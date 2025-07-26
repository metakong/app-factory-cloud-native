import os
import uuid
import json
from datetime import datetime
from shared.utils import get_logger
from shared.gcp_client import save_to_firestore, get_secret, db
import praw
import google.generativeai as genai

logger = get_logger(__name__)

# --- Reddit Scraper Configuration (Full List) ---
SUBREDDIT_PORTFOLIO = [
    {"name": "lifehacks", "tier": 1}, {"name": "LifeProTips", "tier": 1},
    {"name": "YouShouldKnow", "tier": 1}, {"name": "NoStupidQuestions", "tier": 1},
    {"name": "howto", "tier": 1}, {"name": "IWantToLearn", "tier": 1},
    {"name": "solvethis", "tier": 1}, {"name": "GetMotivated", "tier": 2},
    {"name": "GetDisciplined", "tier": 2}, {"name": "selfimprovement", "tier": 2},
    [cite_start]{"name": "productivity", "tier": 2}, {"name": "ZenHabits", "tier": 2}, # [cite: 133]
    {"name": "personalfinance", "tier": 2}, {"name": "financialindependence", "tier": 2},
    {"name": "Frugal", "tier": 2}, {"name": "povertyfinance", "tier": 2},
    {"name": "careerguidance", "tier": 2}, {"name": "jobs", "tier": 2},
    {"name": "BuyItForLife", "tier": 2}, {"name": "goodvalue", "tier": 2},
    {"name": "Anticonsumption", "tier": 2}, {"name": "minimalism", "tier": 2},
    {"name": "shutupandtakemymoney", "tier": 2}, {"name": "HomeImprovement", "tier": 2},
    {"name": "DIY", "tier": 2}, {"name": "homemaking", "tier": 2},
    {"name": "organization", "tier": 2}, {"name": "declutter", "tier": 2},
    [cite_start]{"name": "Parenting", "tier": 2}, {"name": "daddit", "tier": 2}, # [cite: 134]
    {"name": "mommit", "tier": 2}, {"name": "relationships", "tier": 2},
    {"name": "relationship_advice", "tier": 2}, {"name": "travel", "tier": 2},
    {"name": "Fitness", "tier": 2}, {"name": "EatCheapAndHealthy", "tier": 2},
    {"name": "cookingforbeginners", "tier": 2}, {"name": "MealPrepSunday", "tier": 2},
    {"name": "gardening", "tier": 2}, {"name": "SkincareAddiction", "tier": 2},
    {"name": "hobbies", "tier": 2}, {"name": "mildlyinfuriating", "tier": 2},
    {"name": "CrappyDesign", "tier": 2}, {"name": "rant", "tier": 2},
    {"name": "offmychest", "tier": 2}, {"name": "talesfromretail", "tier": 2},
    [cite_start]{"name": "firstworldproblems", "tier": 2}, {"name": "Showerthoughts", "tier": 1}, # [cite: 135]
    {"name": "CrazyIdeas", "tier": 1}, {"name": "SomebodyMakeThis", "tier": 1},
    {"name": "Lightbulb", "tier": 1}
]

SEARCH_TERMS = [
    "is there a tool for", "easier way to", "app that does", "I wish there was an app",
    "how do I fix", "solve this", "help me figure out", "what to do if",
    "the hardest part is", "I'm struggling with", "I hate how",
    "wouldn't it be cool if", "make this", "I would pay for", "needed invention"
]

# --- Gemini Configuration ---
genai.configure()
SUMMARIZATION_MODEL = genai.GenerativeModel('gemini-pro')
SUMMARIZATION_PROMPT = """
[cite_start]Summarize the core problem, unmet need, or product idea from the following text, which was extracted from a public online forum. [cite: 136]
[cite_start]The summary should be a single, concise sentence. [cite: 137]
Focus only on the abstract concept.
[cite_start]CRITICALLY IMPORTANT: Do not include any personal details, names, locations, or conversational filler from the original text. [cite: 138]
TEXT TO SUMMARIZE:
---
{text_content}
---
"""

def get_reddit_client():
    """Initializes and returns an authenticated PRAW client."""
    try:
        creds_json = get_secret("reddit-app-credentials")
        if not creds_json:
            logger.error("Failed to retrieve Reddit credentials from Secret Manager.")
            return None
        creds = json.loads(creds_json)
        return praw.Reddit(
            [cite_start]client_id=creds["client_id"], # [cite: 140]
            client_secret=creds["client_secret"],
            password=creds["password"],
            user_agent=creds["user_agent"],
            username=creds["username"]
        )
    except Exception as e:
        logger.error(f"Error initializing Reddit client: {e}")
        return None

def summarize_content(title: str, body: str) -> str:
    [cite_start]"""Uses Gemini to summarize the user content into a single-sentence idea.""" # [cite: 141]
    full_text = f"Title: {title}\n\nBody: {body}"
    prompt = SUMMARIZATION_PROMPT.format(text_content=full_text)
    try:
        response = SUMMARIZATION_MODEL.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini summarization failed: {e}")
        return title

def is_previously_rejected(summary: str) -> bool:
    """Checks if an idea with the same summary exists in the rejected collection."""
    try:
        [cite_start]rejected_ref = db.collection("rejected_app_ideas").where("description", "==", summary).limit(1).stream() # [cite: 142]
        return any(rejected_ref) # Returns True if the iterator is not empty
    except Exception as e:
        logger.error(f"Error checking for rejected ideas: {e}")
        return False # Fail open to avoid blocking new ideas if check fails

def scrape_subreddit(reddit, subreddit_name):
    """Scrapes, summarizes, and stores ideas from a single subreddit."""
    logger.info(f"Scraping subreddit: r/{subreddit_name}")
    subreddit = reddit.subreddit(subreddit_name)
    found_ideas = 0
    
    [cite_start]query = " OR ".join(f'"{term}"' for term in SEARCH_TERMS) # [cite: 143]
    
    for submission in subreddit.search(query, sort="new", time_filter="month", limit=50):
        if submission.score < 3 or not submission.selftext:
            continue

        summary = summarize_content(submission.title, submission.selftext)

        # --- START: NEW REJECTION CHECK ---
        if is_previously_rejected(summary):
            [cite_start]logger.info(f"Skipping previously rejected idea: {summary}") # [cite: 144]
            continue
        # --- END: NEW REJECTION CHECK ---

        idea_id = f"idea-{uuid.uuid4()}"
        app_idea_data = {
            "idea_id": idea_id,
            "status": "PENDING_VETTING",
            "source_url": f"https://www.reddit.com{submission.permalink}",
            "description": summary,
            [cite_start]"community_validation_score": submission.score, # [cite: 145]
            "community_validation_comments": submission.num_comments,
            "source_subreddit": subreddit_name,
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            save_to_firestore("app_ideas", idea_id, app_idea_data)
            [cite_start]logger.info(f"Saved summarized idea from r/{subreddit_name}: {summary}") # [cite: 146]
            found_ideas += 1
        except Exception as e:
            logger.error(f"Failed to save idea {idea_id} to Firestore: {e}")
            
    logger.info(f"Found and processed {found_ideas} new ideas in r/{subreddit_name}.")

def main():
    """Main function for the web scraper Cloud Run Job."""
    logger.info("Robust Web Scraper Tool job started.")
    [cite_start]reddit_client = get_reddit_client() # [cite: 147]
    if not reddit_client:
        return

    for sub in SUBREDDIT_PORTFOLIO:
        try:
            scrape_subreddit(reddit_client, sub["name"])
        except Exception as e:
            logger.error(f"Failed to scrape r/{sub['name']}: {e}")

    logger.info("Robust Web Scraper Tool job finished.")

if __name__ == "__main__":
    main()