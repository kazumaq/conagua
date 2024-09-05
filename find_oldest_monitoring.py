import requests
import time
from datetime import datetime, timedelta
import random


from logger_config import setup_logging

logger = setup_logging(__name__)

def get_dam_report(date):
    url = f'https://sinav30.conagua.gob.mx:8080/PresasPG/presas/reporte/{date}'
    try:
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 and response.json() else None
    except (requests.RequestException, ValueError):
        return None

def find_oldest_record(max_retries=3):
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365*50)  # Start with 50 years ago
    
    oldest_valid_date = None
    continuous_empty_count = 0
    max_continuous_empty = 30  # Maximum number of continuous empty dates before considering it the end

    while start_date <= end_date:
        mid_date = start_date + (end_date - start_date) // 2
        date_str = mid_date.strftime('%Y-%m-%d')
        
        print(f"Checking date: {date_str}")
        
        # Try up to max_retries times
        for _ in range(max_retries):
            report = get_dam_report(date_str)
            if report is not None:
                break
            time.sleep(random.uniform(1, 3))  # Random delay between retries
        
        if report:
            oldest_valid_date = mid_date
            end_date = mid_date - timedelta(days=1)
            continuous_empty_count = 0
        else:
            start_date = mid_date + timedelta(days=1)
            continuous_empty_count += 1
            if continuous_empty_count >= max_continuous_empty:
                break  # Consider this the end of available data
        
        time.sleep(random.uniform(1, 3))  # Be nice to the server with random delay

    return verify_oldest_date(oldest_valid_date) if oldest_valid_date else None

def verify_oldest_date(candidate_date, num_checks=5):
    print(f"Verifying candidate oldest date: {candidate_date}")
    verified_date = candidate_date
    
    for _ in range(num_checks):
        # Check a random date up to 30 days before the candidate date
        random_days = random.randint(1, 30)
        check_date = candidate_date - timedelta(days=random_days)
        date_str = check_date.strftime('%Y-%m-%d')
        
        print(f"Verifying date: {date_str}")
        report = get_dam_report(date_str)
        
        if report:
            verified_date = check_date
            print(f"Found earlier date: {verified_date}")
        
        time.sleep(random.uniform(1, 3))
    
    return verified_date

if __name__ == "__main__":
    oldest_date = find_oldest_record()
    if oldest_date:
        print(f"The oldest available record is from: {oldest_date}")
        print("Sample data:")
        print(get_dam_report(oldest_date.strftime('%Y-%m-%d')))
    else:
        print("No valid records found in the search range.")