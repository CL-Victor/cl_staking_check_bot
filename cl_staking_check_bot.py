import requests
from requests_oauthlib import OAuth1
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twitter API credentials
consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
access_token = os.environ.get("ACCESS_TOKEN_BOT")
access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET_BOT")

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

# Main logic
def main():
    auth = connect_to_oauth(consumer_key, consumer_secret, access_token, access_token_secret)
    max_pool_value = 40875000  # Maximum pool value in LINK
    last_known_value = max_pool_value

    # Fetch current staking data
    current_value = fetch_staking_data()

    if current_value is None or current_value == max_pool_value:
        # Skip if value is unreadable or full pool
        print("No changes detected or pool is full.")
        return

    if current_value < last_known_value:
        # Calculate available staking amount
        available_for_staking = max_pool_value - current_value
        formatted_value = f"{available_for_staking:,}"  # Format with commas
        message = (
            f"⚠️ LINK Staking pool alert:\n"
            f"{formatted_value} LINK available for staking.\n"
            f"Stake at https://staking.chain.link/\n\n"
            f"$LINK #chainlink"
        )
        post_to_twitter(message, auth)
    else:
        print("No staking opportunity detected.")

if __name__ == "__main__":
    main()
