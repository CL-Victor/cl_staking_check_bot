import requests
from requests_oauthlib import OAuth1
import os

# Twitter API credentials (retrieved from environment variables in GitHub Actions)
consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_TOKEN_BOT")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET_BOT")

# File to store the last posted staking amount
LAST_POSTED_FILE = "last_posted.txt"

# OAuth connection
def connect_to_oauth(consumer_key, consumer_secret, access_token, access_token_secret):
    return OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)

# Function to fetch staking pool data
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

# Function to post a tweet
def post_to_twitter(message, auth):
    url = "https://api.twitter.com/2/tweets"
    payload = {"text": message}
    response = requests.post(url, auth=auth, json=payload)
    if response.status_code != 201:
        print(f"Failed to post tweet: {response.status_code}, {response.text}")
    else:
        print("Tweet posted successfully.")

# Function to get the last posted staking amount
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

# Function to save the last posted staking amount
def save_last_posted_amount(amount):
    with open(LAST_POSTED_FILE, "w") as file:
        file.write(str(amount))
    print(f"Saved last posted amount: {amount} LINK")

# Main logic
def main():
    auth = connect_to_oauth(consumer_key, consumer_secret, access_token, access_token_secret)
    max_pool_value = 40875000  # Maximum pool value in LINK

    # Fetch current staking data
    current_value = fetch_staking_data()

    if current_value is None or current_value == max_pool_value:
        # Skip if value is unreadable or full pool
        print("No changes detected or pool is full.")
        return

    # Calculate available staking amount if pool value decreases
    available_for_staking = max_pool_value - current_value

    # Check the last posted amount
    last_posted_amount = get_last_posted_amount()
    if last_posted_amount == available_for_staking:
        print(f"No changes since the last post: {available_for_staking} LINK available.")
        return

    # Format the message and post to Twitter
    formatted_value = f"{available_for_staking:,}"  # Format with commas
    message = (
        f"⚠️ LINK Staking pool alert: {formatted_value} $LINK available for staking.\n"
        f"⏩ Stake at https://staking.chain.link/\n\n"
        f"#Chainlink"
    )
    post_to_twitter(message, auth)

    # Save the current amount as the last posted amount
    save_last_posted_amount(available_for_staking)

if __name__ == "__main__":
    # Ensure LAST_POSTED_FILE exists if cached
    if not os.path.exists(LAST_POSTED_FILE):
        with open(LAST_POSTED_FILE, "w") as f:
            f.write("")  # Create an empty file if it doesn't exist
    main()
