import requests
import json
import os
from datetime import datetime, timedelta
import time
import logging
from tqdm import tqdm

# Set up logging to both file and console
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler('dam_data_fetch.log')
    file_formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logging()

def get_dam_report(date):
    url = f'https://sinav30.conagua.gob.mx:8080/PresasPG/presas/reporte/{date}'
    try:
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 and response.json() else None
    except (requests.RequestException, ValueError):
        return None

def save_data(data, date):
    folder = 'dam_data'
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f'{date}.json')
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def is_valid_data(data):
    return isinstance(data, list) and len(data) > 0 and all(isinstance(item, dict) for item in data)

def load_cached_data(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data if is_valid_data(data) else None
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def process_date(date):
    date_str = date.strftime('%Y-%m-%d')
    filename = os.path.join('dam_data', f'{date_str}.json')
    
    # Check cache first
    cached_data = load_cached_data(filename)
    if cached_data:
        logger.info(f"Using cached data for {date_str}")
        return True, False  # Data found, but not freshly fetched
    
    # If not in cache or invalid, fetch from API
    data = get_dam_report(date_str)
    if data:
        save_data(data, date_str)
        logger.info(f"Data fetched and saved for {date_str}")
        return True, True  # Data found and freshly fetched
    else:
        logger.info(f"No data found for {date_str}")
        return False, True  # No data found, but API was called

def main():
    current_date = datetime.now().date()
    days_processed = 0
    days_with_data = 0
    api_calls = 0

    with tqdm(desc="Processing dates", unit="day") as pbar:
        while True:
            data_found, api_called = process_date(current_date)
            
            if data_found:
                days_with_data += 1
            if api_called:
                api_calls += 1
            days_processed += 1
            
            pbar.update(1)
            pbar.set_postfix({
                'Date': current_date.strftime('%Y-%m-%d'),
                'Data Found': f"{days_with_data}/{days_processed}",
                'Success Rate': f"{days_with_data/days_processed:.2%}",
                'API Calls': api_calls
            })

            current_date -= timedelta(days=1)
            if api_called:
                time.sleep(0.25)  # Only wait if an API call was made

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script stopped by user.")
        print("\nScript stopped by user. Check dam_data_fetch.log for full details.")