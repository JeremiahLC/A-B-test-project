import time
import random
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient 

# MongoDB connection configuration
MONGO_CONNECTION_STRING = "mongodb+srv://jeremiahliulc_db_user:xxxxxxxxxxx@ab-test-cluster.vo4w9me.mongodb.net/?retryWrites=true&w=majority&appName=AB-test-cluster"
client = MongoClient(MONGO_CONNECTION_STRING)
db = client['ab_test_project']
comments_collection = db['user_comments']

# Predefined comments for different versions to simulate realistic user feedback
COMMENTS_A = [
    "The blue button is okay, I guess.",
    "Didn't really notice the button color.",
    "It's just a button.",
    "Felt a bit hard to see the button against the background."
]
COMMENTS_B = [
    "Wow, the green button really pops! Very clear.",
    "I love the new green color, it's very inviting.",
    "The green button made it easy to know where to click.",
    "This design looks much more professional and trustworthy."
]

# Tags for categorizing user feedback
TAGS_A = ["confusing", "hard_to_see", "plain_design"]
TAGS_B = ["clear_call_to_action", "good_design", "easy_to_use", "trustworthy"]

# Configuration constants for the A/B test simulation
BASE_URL = "https://jeremiahlc.github.io/A-B-test-project/"
URL_A = BASE_URL
URL_B = BASE_URL + "version_b.html"
BUTTON_ID = "buy-button"
VISITORS_PER_VERSION = 500 
CONVERSION_RATE_A = 0.03
CONVERSION_RATE_B = 0.05
COMMENT_PROBABILITY = 0.68  # Probability that a converting user leaves feedback

# Diverse user agents to simulate different devices and browsers
USER_AGENTS = [
    # Windows 10 (Chrome, Edge, Firefox)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.69",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0",
    
    # macOS (Chrome, Safari)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    
    # iPhone (Safari)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    
    # Android (Chrome - Pixel, Samsung)
    "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A536U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    
    # iPad (Safari)
    "Mozilla/5.0 (iPad; CPU OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    
    # Linux (Chrome)
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
]


def simulate_visit(url, version_name, conversion_rate):
    """
    Simulates a single user visit to the specified URL with given conversion rate
    
    Args:
        url (str): The URL to visit (A or B version)
        version_name (str): Name of the test version for tracking
        conversion_rate (float): Probability of user converting (clicking button)
    """
    
    # Generate unique user ID for tracking
    user_id = str(uuid.uuid4())

    # Configure Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    chrome_options.add_argument('--headless')  # Run without GUI
    chrome_options.add_argument('--log-level=3')  # Suppress logs
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize Chrome driver
    service = Service(executable_path='chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Record start time for conversion timing
        start_time = time.time()
        driver.get(url)
        print(f"Visiting: {driver.title} (User ID: ...{user_id[-12:]})")
        
        # Simulate user hesitation before potential conversion
        hesitation_time = random.uniform(2, 10)
        time.sleep(hesitation_time)
        
        # Determine if user converts based on conversion rate
        if random.random() < conversion_rate:
            driver.find_element(By.ID, BUTTON_ID).click()
            print(f"--- Conversion successful! Clicked {BUTTON_ID} ---")
            
            # Calculate time taken to convert
            time_to_convert = time.time() - start_time
            
            print("...Waiting for GTM to send events...")
            time.sleep(5)  # Allow time for GA4 events to be sent
            
            # Randomly decide if user leaves qualitative feedback
            if random.random() < COMMENT_PROBABILITY:
                # Select appropriate comment based on version
                comment_text = random.choice(COMMENTS_A if version_name == 'Version A' else COMMENTS_B)
                
                # Generate version-specific ratings and tags
                if version_name == 'Version A':
                    star_rating = random.randint(1, 3)  # Lower ratings for Version A
                    tags = random.sample(TAGS_A, k=random.randint(1, len(TAGS_A)))
                else:
                    star_rating = random.randint(3, 5)  # Higher ratings for Version B
                    tags = random.sample(TAGS_B, k=random.randint(1, len(TAGS_B)))

                # Create feedback document for MongoDB
                comment_document = {
                    "user_pseudo_id": user_id,
                    "test_version": version_name,
                    "comment_text": comment_text,
                    "star_rating": star_rating,
                    "tags": tags,
                    "time_to_convert_seconds": round(time_to_convert, 2),
                    "timestamp": time.time()
                }
                
                # Store feedback in MongoDB
                comments_collection.insert_one(comment_document)
                print(f"--- User provided detailed feedback stored in MongoDB: {star_rating} stars, tags: {tags} ---")

        else:
            print("Visitor did not convert, leaving page.")
            
    except Exception as e:
        raise e
    finally:
        # Always close the browser
        driver.quit()


if __name__ == "__main__":
    # Create balanced visit queue with equal distribution
    visit_queue = (['A'] * VISITORS_PER_VERSION) + (['B'] * VISITORS_PER_VERSION)
    random.shuffle(visit_queue)  # Randomize visit order
    total_to_run = len(visit_queue)
    
    print(f"--- Starting simulation of {total_to_run} visits (with advanced NoSQL integration) ---")
    
    # Process each visit in the queue
    for i, version in enumerate(visit_queue):
        print(f"\n[Visitor {i + 1} / {total_to_run}] -> Assigned to group {version}")
        try:
            if version == 'A':
                simulate_visit(URL_A, 'Version A', CONVERSION_RATE_A)
            else:
                simulate_visit(URL_B, 'Version B', CONVERSION_RATE_B)
        except Exception as e:
            print(f"!!!!!! [Visitor {i + 1}] Failed! Error: {e} !!!!!!")
            time.sleep(10)  # Wait before retrying after error
        
        # Random delay between visits to simulate natural traffic
        time.sleep(random.uniform(3, 10))
        
    print("\n--- All simulation visits completed ---")
    client.close()  # Close MongoDB connection
