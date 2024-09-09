from dotenv import load_dotenv
import os
import tweepy
import sqlite3
import argparse
from datetime import datetime
import pytz

from logger_config import setup_logging

load_dotenv()

logger = setup_logging(__name__)

# Twitter API credentials from environment variables
consumer_key = os.getenv('TWITTER_API_KEY')
consumer_secret = os.getenv('TWITTER_API_SECRET')
access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

# Authenticate with Twitter
auth = tweepy.OAuth1UserHandler(
    consumer_key, 
    consumer_secret,
    access_token, 
    access_token_secret
  )
api = tweepy.API(auth)
client = tweepy.Client(
    consumer_key=consumer_key, 
    consumer_secret=consumer_secret,
    access_token=access_token, 
    access_token_secret=access_token_secret
  )
#client = tweepy.Client(bearer_token)

def get_chapala_data():
    conn_static = sqlite3.connect('reservoir_static.db')
    conn_dynamic = sqlite3.connect('reservoir_dynamic.db')
    
    cursor_static = conn_static.cursor()
    cursor_dynamic = conn_dynamic.cursor()

    # Get max volume from static data
    cursor_static.execute("SELECT namoalmac FROM reservoirs WHERE clavesih = 'LDCJL'")
    max_volume = cursor_static.fetchone()[0]

    # Get current date in Mexico City timezone
    mexico_tz = pytz.timezone('America/Mexico_City')
    current_date = datetime.now(mexico_tz).date()

    # Get most recent data
    cursor_dynamic.execute("""
        SELECT fechamonitoreo, almacenaactual, elevacionactual
        FROM reservoir_data
        WHERE clavesih = 'LDCJL' AND fechamonitoreo <= ?
        ORDER BY fechamonitoreo DESC
        LIMIT 2
    """, (current_date,))

    rows = cursor_dynamic.fetchall()
    if len(rows) < 2:
        raise ValueError("Not enough data available")

    current_data, previous_data = rows

    conn_static.close()
    conn_dynamic.close()

    return max_volume, current_data, previous_data

def format_message(max_volume, current_data, previous_data):
    current_date, current_volume, current_elevation = current_data
    previous_date, previous_volume, previous_elevation = previous_data

    current_percentage = (current_volume / max_volume) * 100
    volume_change = current_volume - previous_volume
    height_change = (current_elevation - previous_elevation) * 100  # Convert to cm
    percentage_change = ((current_volume - previous_volume) / max_volume) * 100

    change_arrow = "🔼" if volume_change > 0 else "🔽"

    message = f"""#LagoDeChapala
Volumen actual: {current_volume:.2f} hm³  ({current_percentage:.2f}%)
Cambios desde el {previous_date}:
{change_arrow} {abs(volume_change):.2f} hm³    →    {abs(height_change):.2f} cm    →    {abs(percentage_change):.2f}%

📈 Ver gráfica https://www.gdlmx.com/embalses/niveles
#Chapala #LDCJL #Jalisco"""

    return message

def verify_twitter_credentials() -> bool:
    try:
        api.verify_credentials()
        logger.info("Twitter credentials are valid.")
        return True
    except tweepy.errors.Unauthorized as e:
        logger.error(f"Twitter credentials verification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during credential verification: {e}")
        return False

def post_tweet(tweet: str) -> bool:
    try:
        response = client.create_tweet(text=tweet)
        logger.info(f"https://x.com/user/status/{response.data['id']}")
        logger.info(f"Tweet posted successfully. Tweet ID: {response.data['id']}")
        return True
    except tweepy.errors.Forbidden as e:
        logger.error(f"Error posting tweet: Forbidden. This might be due to insufficient API access level.")
        logger.error(f"Full error message: {e}")
        logger.info("Please check your Twitter Developer account and ensure you have the necessary permissions to post tweets.")
        return False
    except tweepy.errors.TweepError as e:
        logger.error(f"Error posting tweet: {e}")
        logger.debug(f"Full error object: {e.api_errors if hasattr(e, 'api_errors') else str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error posting tweet: {e}")
        return False

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Lago de Chapala status update")
    parser.add_argument("--dry-run", action="store_true", help="Print the message without sending")
    parser.add_argument("--test-credentials", action="store_true", help="Test Twitter API credentials")
    args = parser.parse_args()

    if args.test_credentials:
        verify_twitter_credentials()
        return

    try:
        logger.info("Fetching Chapala data...")
        max_volume, current_data, previous_data = get_chapala_data()
        logger.info("Formatting message...")
        message = format_message(max_volume, current_data, previous_data)

        if args.dry_run:
            logger.info("Dry run: Message content:")
            logger.info(message)
        else:
            logger.info("Attempting to post tweet...")
            if verify_twitter_credentials():
                if post_tweet(message):
                    logger.info("Tweet posted successfully.")
                else:
                    logger.error("Failed to post tweet.")
            else:
                logger.error("Twitter credentials are invalid. Tweet not posted.")
    except ValueError as e:
        logger.error(f"Data error: {e}")
    except tweepy.errors.TweepError as e:
        logger.error(f"Twitter API error: {e}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
