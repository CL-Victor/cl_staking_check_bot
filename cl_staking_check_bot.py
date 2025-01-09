import os
import requests
from requests_oauthlib import OAuth1

# Twitter API credentials (retrieved from environment variables in GitHub Actions)
consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_TOKEN_BOT")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET_BOT")

# File to store the last posted staking amount
LAST_POSTED_FILE = "last_posted.txt"
GIF_FILE = "LINK_diamondhand.gif"  # GIF located in the root of the repo

def connect_to_oauth(consumer_key, consumer_secret, access_token, access_token_secret):
    """
    Establish OAuth1 connection.
    """
    return OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)

def post_to_twitter(message, gif_file, auth):
    """
    Posts a tweet with or without an attached GIF.
    """
    media_id = None
    if gif_file and os.path.exists(gif_file):
        try:
            print(f"Uploading media: {gif_file}")
            upload_url = "https://upload.twitter.com/1.1/media/upload.json"
            with open(gif_file, "rb") as file:
                files = {"media": file}
                response = requests.post(upload_url, auth=auth, files=files)
                print(f"Upload response: {response.status_code}, {response.text}")
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
    print(f"Tweet response: {response.status_code}, {response.text}")
    if response.status_code != 201:
        print(f"Failed to post tweet: {response.status_code}, {response.text}")
    else:
        print("Tweet posted successfully.")

def get_last_posted_amount():
    """
    Retrieves the last posted staking amount from the file.
    """
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
    """
    Saves the last posted staking amount to the file.
    """
    with open(LAST_POSTED_FILE, "w") as file:
        file.write(str(amount))
    print(f"Saved last posted amount: {amount} LINK")

def fetch_staking_data():
    """
    Fetches the current staking pool data from the Chainlink API.
    """
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
    """
    Main function to post staking pool alerts to Twitter.
    """
    auth = connect_to_oauth(consumer_key, consumer_secret, access_token, access_token_secret)
    max_pool_value = 40875000  # Maximum pool value in LINK

    # Fetch current staking data
    current_value = fetch_staking_data()

    if current_value is None or current_value == max_pool_value:
        print("No changes detected or pool is full.")
        return

    available_for_staking = max_pool_value - current_value

    # Check if available amount is below the threshold
    if available_for_staking < 50:
        print(f"Available amount ({available_for_staking} LINK) is less than 50. Skipping tweet.")
        return

    last_posted_amount = get_last_posted_amount()
    if last_posted_amount == available_for_staking:
        print(f"No changes since the last post: {available_for_staking} LINK available.")
        return

    # Prepare the tweet message
    message = f"🔥 LINK Staking Pool Update: {available_for_staking:,} $LINK available to stake! 🔓\n💎 Stake now: https://staking.chain.link/\n\n#Chainlink"

    # Post the tweet with the GIF
    post_to_twitter(message, GIF_FILE, auth)

    # Save the current amount as the last posted amount
    save_last_posted_amount(available_for_staking)

if __name__ == "__main__":
    main()
