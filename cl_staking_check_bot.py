import asyncio
import os
import requests
from pyppeteer import launch
from PIL import Image
from requests_oauthlib import OAuth1

# Website URL and output files
URL = "https://staking.chain.link/"
SCREENSHOT_FILE = "screenshot.png"
CROPPED_FILE = "cropped_screenshot.png"

# Twitter API credentials (retrieved from environment variables in GitHub Actions)
consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_TOKEN_BOT")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET_BOT")

# File to store the last posted staking amount
LAST_POSTED_FILE = "last_posted.txt"

def clean_existing_screenshots(*files):
    """
    Deletes existing screenshot files if they exist.
    """
    for file in files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Deleted existing file: {file}")
        else:
            print(f"No existing file to delete: {file}")

async def capture_screenshot(url, output_file):
    """
    Captures a screenshot of the given URL after a fixed delay.
    """
    print(f"Opening {url}...")
    try:
        browser = await launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = await browser.newPage()

        # Set the viewport size to capture a larger portion of the page
        await page.setViewport({"width": 1920, "height": 1080})

        # Navigate to the website
        await page.goto(url)
        print("Waiting for 3 seconds to ensure the page loads...")
        await asyncio.sleep(3)  # Wait for 3 seconds

        # Take a screenshot
        print(f"Saving screenshot to {output_file}...")
        await page.screenshot({"path": output_file, "fullPage": True})

        await browser.close()
        print("Screenshot captured successfully.")
        return True
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return False

def crop_screenshot(input_file, output_file, crop_box):
    """
    Crops the given screenshot to the specified dimensions.
    """
    try:
        print(f"Cropping screenshot: {input_file}")
        with Image.open(input_file) as img:
            cropped_img = img.crop(crop_box)
            cropped_img.save(output_file)
        print(f"Cropped screenshot saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error cropping screenshot: {e}")
        return False

def connect_to_oauth(consumer_key, consumer_secret, access_token, access_token_secret):
    return OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)

def post_to_twitter(message, media_file, auth):
    """
    Posts a tweet with or without an attached image.
    """
    media_id = None
    if media_file and os.path.exists(media_file):
        try:
            print(f"Uploading media: {media_file}")
            upload_url = "https://upload.twitter.com/1.1/media/upload.json"
            with open(media_file, "rb") as file:
                files = {"media": file}
                response = requests.post(upload_url, auth=auth, files=files)
                if response.status_code == 200:
                    media_id = response.json()["media_id_string"]
                    print(f"Media uploaded successfully: {media_id}")
                else:
                    print(f"Failed to upload media: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Error uploading media: {e}")

    # Post the tweet
    print("Posting tweet...")
    tweet_url = "https://api.twitter.com/2/tweets"
    payload = {"text": message}
    if media_id:
        payload["media"] = {"media_ids": [media_id]}
    response = requests.post(tweet_url, auth=auth, json=payload)
    if response.status_code != 201:
        print(f"Failed to post tweet: {response.status_code}, {response.text}")
    else:
        print("Tweet posted successfully.")

def get_last_posted_amount():
    if os.path.exists(LAST_POSTED_FILE):
        with open(LAST_POSTED_FILE, "r") as file:
            try:
                amount = int(file.read().strip())
                print(f"Last posted amount read from file: {amount} LINK")
                return amount
            except ValueError:
                print("Error reading last posted amount. File content is invalid.")
                return None
    print("No previous posted amount found. File does not exist.")
    return None

def save_last_posted_amount(amount):
    with open(LAST_POSTED_FILE, "w") as file:
        file.write(str(amount))
    print(f"Saved last posted amount: {amount} LINK")

def fetch_staking_data():
    url = "https://staking.chain.link/api/query?query=STAKING_POOL_TOTAL_PRINCIPAL_QUERY&variables=%7B%22schemaName%22%3A%22ethereum-mainnet%22%2C%22contractAddress%22%3A%220xBc10f2E862ED4502144c7d632a3459F49DFCDB5e%22%7D"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        total_principal = data['data']['allStakingv02StakingPoolPrincipals']['nodes'][0]['totalPrincipal']
        return int(total_principal) // 10**18  # Convert to integer in LINK
    except Exception as e:
        print(f"Error fetching staking data: {e}")
        return None

def main():
    auth = connect_to_oauth(consumer_key, consumer_secret, access_token, access_token_secret)
    max_pool_value = 40875000  # Maximum pool value in LINK

    # Fetch current staking data
    current_value = fetch_staking_data()

    if current_value is None or current_value == max_pool_value:
        print("No changes detected or pool is full.")
        return

    available_for_staking = max_pool_value - current_value
    last_posted_amount = get_last_posted_amount()
    if last_posted_amount == available_for_staking:
        print(f"No changes since the last post: {available_for_staking} LINK available.")
        return

    # Step 1: Clean up existing screenshots
    clean_existing_screenshots(SCREENSHOT_FILE, CROPPED_FILE)

    # Step 2: Capture a new screenshot
    screenshot_success = asyncio.get_event_loop().run_until_complete(capture_screenshot(URL, SCREENSHOT_FILE))

    # Step 3: Crop the new screenshot (only if the screenshot succeeded)
    crop_success = False
    if screenshot_success:
        crop_box = (1970, 235, 2400, 600)  # Updated crop box
        crop_success = crop_screenshot(SCREENSHOT_FILE, CROPPED_FILE, crop_box)

    # Step 4: Post to Twitter with or without an image
    message = f"⚠️ LINK Staking pool alert: {available_for_staking:,} LINK available for staking.\n⏩ Stake at https://staking.chain.link/\n\n#Chainlink"
    post_to_twitter(message, CROPPED_FILE if crop_success else None, auth)

    # Step 5: Save the current amount as the last posted amount
    save_last_posted_amount(available_for_staking)

if __name__ == "__main__":
    main()
