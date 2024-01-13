import logging
from firefly_api import FireflyIIIAPI
from kresus import Kresus
from utils import test_create_get_delete_fireflyapi, get_local_transaction, update_local_to_firefly, dump_transaction_to_csv, check_kersus_firefly_accout
from logging_config import setup_logging
from dotenv import load_dotenv
import os

def main():
    # Set up logging
    setup_logging()

    logger = logging.getLogger(__name__)

    # Load environment variables from .env file
    load_dotenv()

    # Accessing variables
    base_api_url = os.getenv('FIREBASE_URL')
    api_token = os.getenv('API_TOKEN')

    # If the variables are not found in .env, fall back to a default value or another env variable
    base_api_url = base_api_url or os.getenv('F3S_FIREBASE_URL', "https://your-firefly-instance.com/api/v1")
    api_token = api_token or os.getenv('F3S_API_TOKEN', "your_api_token")

    logger.info(f"base_api_url for firefly-iii : {base_api_url}")
    logger.info(f"Firefly API token : {api_token}")

    # Initialize Firefly III API wrapper
    firefly_api = FireflyIIIAPI(base_api_url, api_token)
    # full testing of the firefly api
    test_create_get_delete_fireflyapi(firefly_api)
    
    # Initialize Kresus instance
    kresus = Kresus()
    kresus.get_all_kresus()
    check_kersus_firefly_accout(firefly_api, kresus)

    # Sync data from Kresus to Firefly III
    kresus.parse_account()
    kresus.parse_transactions(date="2024-01-01")

    # Implement sync logic here (e.g., update_kresus_to_firefly())

    # Update local data to Firefly III
    local_transactions = get_local_transaction()
    firefly_transactions = firefly_api.list_transactions()
    update_local_to_firefly(firefly_api, local_transactions, firefly_transactions)

    # Optionally, dump transactions to a CSV file
    dump_transaction_to_csv(firefly_transactions, "transactions.csv")
    


if __name__ == "__main__":
    main()
