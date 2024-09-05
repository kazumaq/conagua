import requests
import json
import os
from datetime import datetime, timedelta
import time
import logging
from tqdm import tqdm
import argparse
import sys
from logger_config import setup_logging

logger = setup_logging(__name__)

def test_connection():
    try:
        response = requests.get('https://sinav30.conagua.gob.mx:8080', timeout=10)
        logger.info(f"Connection test result: Status code {response.status_code}")
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False

def get_dam_report(date):
    url = f'https://sinav30.conagua.gob.mx:8080/PresasPG/presas/reporte/{date}'
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json() if response.json() else None
        else:
            logger.error(f"Failed to fetch data. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None
    except requests.RequestException as e:
        logger.error(f"Request exception occurred: {str(e)}")
        return None
    except ValueError as e:
        logger.error(f"JSON decoding failed: {str(e)}")
        return None

def save_data(data, date):
    folder = 'dam_data'
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f'{date}.json')
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Data saved successfully to {filename}")
    except IOError as e:
        logger.error(f"Failed to save data to {filename}: {str(e)}")
        raise

def is_valid_data(data):
    if not isinstance(data, list):
        logger.error("Data is not a list")
        return False
    if len(data) == 0:
        logger.error("Data list is empty")
        return False
    if not all(isinstance(item, dict) for item in data):
        logger.error("Not all items in the data list are dictionaries")
        return False
    return True

def load_cached_data(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        if is_valid_data(data):
            return data
        else:
            logger.error(f"Invalid data structure in cached file: {filename}")
            return None
    except FileNotFoundError:
        logger.info(f"Cached file not found: {filename}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error in cached file {filename}: {str(e)}")
        return None

def process_date(date):
    date_str = date.strftime('%Y-%m-%d')
    filename = os.path.join('dam_data', f'{date_str}.json')
    
    cached_data = load_cached_data(filename)
    if cached_data:
        logger.info(f"Using cached data for {date_str}")
        return True, False  # Data found, but not freshly fetched
    
    data = get_dam_report(date_str)
    if data:
        if is_valid_data(data):
            save_data(data, date_str)
            logger.info(f"Data fetched and saved for {date_str}")
            return True, True  # Data found and freshly fetched
        else:
            logger.error(f"Invalid data structure received for {date_str}")
            return False, True
    else:
        logger.info(f"No data found for {date_str}")
        return False, True  # No data found, but API was called

def main(start_date, all_dates):
    current_date = start_date
    days_processed = 0
    days_with_data = 0
    api_calls = 0
    fresh_data_fetched = False

    with tqdm(desc="Processing dates", unit="day") as pbar:
        while True:
            data_found, api_called = process_date(current_date)
            
            if data_found:
                days_with_data += 1
                
            if api_called:
                api_calls += 1
                if data_found:
                    fresh_data_fetched = True
            days_processed += 1
            
            pbar.update(1)
            pbar.set_postfix({
                'Date': current_date.strftime('%Y-%m-%d'),
                'Data Found': f"{days_with_data}/{days_processed}",
                'Success Rate': f"{days_with_data/days_processed:.2%}",
                'API Calls': api_calls
            })

            if not all_dates:
                break

            current_date -= timedelta(days=1)
            if api_called:
                time.sleep(0.25)  # Only wait if an API call was made

    if not fresh_data_fetched:
        logger.warning("No fresh data was fetched. All data was from cache or no data was found.")
        return 1
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch dam data for specific dates.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--today", action="store_true", help="Fetch data for today (default)")
    group.add_argument("--date", type=str, help="Fetch data for a specific date (YYYY-MM-DD)")
    parser.add_argument("--test", action="store_true", help="Test connection to the server")
    parser.add_argument("--all", action="store_true", help="Fetch all dates starting from the specified date or today")

    args = parser.parse_args()

    if args.test:
        if test_connection():
            logger.info("Connection test successful")
            sys.exit(0)
        else:
            logger.error("Connection test failed")
            sys.exit(1)

    if args.date:
        try:
            start_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            logger.error("Invalid date format. Please use YYYY-MM-DD.")
            sys.exit(1)
    else:
        start_date = datetime.now().date()

    try:
        exit_code = main(start_date, args.all)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Script stopped by user.")
        print("\nScript stopped by user. Check dam_data_fetch.log for full details.")
        sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected error occurred:")
        sys.exit(1)