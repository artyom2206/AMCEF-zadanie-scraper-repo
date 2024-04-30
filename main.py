# type: ignore
import asyncio
import json
import logging
import os
import pickle
import time
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from scraper import (get_last_page_number, scrape_all_pages, save_to_json,
                     scrape_all_contract_details, scrape_all_contract_documents,
                     scrape_all_contract_announcements)


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1pugWKXjA1wPkR4-OI39vCXOfgOCWjBJG3qqEzWYXjl4'
RANGE_NAME = 'Hárok1!A2'
GOOGLE_CLIENT_SECRET_JSON = 'client_secret.json'


def setup_logging(debug):
  # Define the logging level
  level = logging.DEBUG if debug else logging.INFO

  # Create a logger
  logger = logging.getLogger()
  logger.setLevel(level)

  # Setup file handler to overwrite the existing file
  # 'w' for overwrite, 'a' for append
  file_handler = logging.FileHandler('scraper.log', mode='w')
  file_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
  file_handler.setFormatter(file_formatter)

  # Setup console handler
  console_handler = logging.StreamHandler()
  console_formatter = logging.Formatter('%(levelname)s - %(message)s')
  console_handler.setFormatter(console_formatter)
  # Only log INFO and above to console, adjust if needed
  console_handler.setLevel(logging.INFO)

  # Clear existing handlers if running this setup multiple times in an interactive environment
  logger.handlers = []

  # Add handlers to the logger
  logger.addHandler(file_handler)
  logger.addHandler(console_handler)


def load_json_data(filepath):
  with open(filepath, 'r') as file:
    data = json.load(file)
  return data


def parse_date(date_str):
  """Parse a date string into a datetime object. Return a default old date if empty or invalid."""
  if not date_str:
    return datetime.min  # Return the minimum datetime if the date is empty
  try:
    return datetime.strptime(date_str, "%d.%m.%Y %H:%M")
  except ValueError:
    return datetime.min


def send_to_sheets(detailed_contracts):
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  logging.info("Sending to google sheets...")
  creds = None

  # Sort contracts by 'Dátum poslednej aktualizácie', falling back to 'Dátum vytvorenia'
  # FIXME: nie je to najlepšie, niektoré nemajú poslednú aktualizáciu
  detailed_contracts.sort(key=lambda x: (parse_date(x.get(
    "Dátum poslednej aktualizácie", "")) or parse_date(x.get("Dátum vytvorenia", ""))), reverse=True)

  # The file token.pickle stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
      creds = pickle.load(token)

  # If no valid credentials are available, let the user log in.
    if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
        try:
          creds.refresh(Request())
        except Exception as e:
          logging.error(f"Failed to refresh access token: {e}")
          os.remove('token.pickle')  # Remove the expired token
          creds = None  # Reset creds and require re-authentication
      if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRET_JSON, SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
          pickle.dump(creds, token)

  service = build('sheets', 'v4', credentials=creds)

  # Prepare data for Google Sheets
  data_to_insert = []
  for item in detailed_contracts:
    row = [
        item.get("URL zákazky", ""),
        item.get("Názov zákazky", ""),
        item.get("Názov obstarávateľa", ""),
        item.get("Dátum vytvorenia", ""),
        item.get("Dátum poslednej aktualizácie", ""),
        item.get("Stav zákazky", ""),
        item.get("CPV zákazky", "").strip().replace('\n', ', '),
        item.get("Druh zákazky", ""),
        item.get("Dátum zverejnenia", ""),
        ', '.join(item.get("Dokumenty", [])),
        ', '.join(item.get("Oznámenia", []))
    ]
    data_to_insert.append(row)

  body = {
      'values': data_to_insert
    }
  result = service.spreadsheets().values().update(
      spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
      valueInputOption='USER_ENTERED', body=body).execute()
  logging.info(f"{result.get('updatedCells')} cells updated.")


async def main():
  setup_logging(debug=True)
  logging.info("Starting the scraper")

  timings = {}
  start_time = time.time()

  base_url = 'https://www.uvo.gov.sk/vyhladavanie/vyhladavanie-zakaziek?cpv=48000000-8+72000000-5+73000000-2'
  last_page = await get_last_page_number(base_url)
  logging.info(f"Scraping from page 1 to {last_page}")
  contracts = await scrape_all_pages(base_url, last_page)
  timings['Scrape all pages'] = time.time() - start_time
  # save_to_json(contracts, 'scraped_data.json')

  start_time = time.time()
  detailed_contracts = await scrape_all_contract_details(contracts)
  timings['Scrape detailed contracts'] = time.time() - start_time
  # save_to_json(detailed_contracts, 'detailed_contracts.json')

  start_time = time.time()
  detailed_contracts_with_documents = await scrape_all_contract_documents(detailed_contracts)
  timings['Scrape contract documents'] = time.time() - start_time
  # save_to_json(detailed_contracts_with_documents,
  #              'detailed_contracts_with_documents.json')

  start_time = time.time()
  full_contracts = await scrape_all_contract_announcements(detailed_contracts_with_documents)
  timings['Scrape contract announcements'] = time.time() - start_time
  # save_to_json(full_contracts, 'full_contracts.json')

  total_time = sum(timings.values())
  timings['Total elapsed time'] = total_time

  logging.info("\nAll timings:")
  for task, duration in timings.items():
    logging.info(f"{task}: {duration:.2f} seconds")

  # full_contracts = load_json_data("full_contracts.json")
  send_to_sheets(full_contracts)

if __name__ == '__main__':
  asyncio.run(main())
