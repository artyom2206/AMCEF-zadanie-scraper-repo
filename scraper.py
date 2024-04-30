import json
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup  # type: ignore

REQUEST_DELAY = 0.1  # 0.1 testované. Pri menších hodnotách je blokovanie scrapera
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3', "Connection": "keep-alive"}


async def fetch(session, url, max_retries=100):
  logging.debug(f"Fetching url: {url}")

  for attempt in range(max_retries):
    try:
      async with session.get(url, headers=HEADERS) as response:
        logging.debug(f"Response from: {url}")
        return await response.text()
    except aiohttp.ClientError as e:
      logging.warning(f"ClientError: {e}")
      logging.warning(f"Attempt {attempt} of {max_retries - 1} for {url}")
      if attempt < max_retries - 1:
        await asyncio.sleep(1 * attempt + 3)
        continue
      else:
        logging.error(f"Out of attempts for url: {url}")
        raise e from None  # Re-raise last exception if all retries fail


async def scrape_page(session, url, check_element="", check_no_records=False, max_retries=10):
  """
  :param check_element: Kontrola elementu cez css selector, ktorý ked sa nenájde, opakuje celý scrape.
  :param check_no_records: Kontrola či tabuľka v dokumentoch alebo oznameniach obsahuje dáta.
  """
  logging.debug(f"Scraping page: {url}")
  for attempt in range(max_retries):
    content = await fetch(session, url)
    soup = BeautifulSoup(content, 'lxml')

    if check_no_records:
      no_records = soup.find('strong', class_='red', text='Žiadny záznam')
      if no_records:
        logging.debug(f"No records found: {url}")
        return soup

    if check_element and not soup.select_one(check_element) and not no_records:
      logging.warning(
          f"Element {check_element} not found on {url}, retrying... {attempt + 1}/{max_retries}")
      await asyncio.sleep(1 * attempt + 3)
      continue
    logging.debug(f"Success: {url}")
    return soup
  logging.error(
    f"Failed to find the required element after {max_retries} retries on {url}")
  return None


async def get_last_page_number(url):
  async with aiohttp.ClientSession() as session:
    soup = await scrape_page(session, url)
    last_page_link = soup.find('a', class_='pag-last')
    last_page_number = int(last_page_link['href'].split('page=')[-1])
    return last_page_number


def parse_table(soup):
  table = soup.find('table', id='lists-table')
  rows = table.find_all('tr')[1:]  # skip the header row
  data = []
  for row in rows:
    cols = row.find_all('td')
    if len(cols) > 1:  # Ensure it's not an empty row
      name_link = cols[0].find('a', class_='ul-link')
      contract_name = name_link.text.strip()
      contract_url = 'https://www.uvo.gov.sk' + name_link['href']
      provider_name = cols[1].find('a', class_='ul-link').text.strip()
      data.append({
          'Názov zákazky': contract_name,
          'URL zákazky': contract_url,
          'Názov obstarávateľa': provider_name
      })
  return data


async def scrape_all_pages(url, last_page):
  # connector = aiohttp.TCPConnector(limit=2)
  # async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
  async with aiohttp.ClientSession() as session:
    tasks = []
    all_data = []

    logging.info("Prepairing to scrape all table pages...")
    await asyncio.sleep(5)

    for page in range(1, last_page + 1):
      logging.debug(f"Creating task for page: {page}")
      page_url = f"{url}&page={page}"
      task = asyncio.create_task(scrape_page(
        session, page_url, "table#lists-table"))
      tasks.append(task)
      await asyncio.sleep(0.1)  # important
    results = await asyncio.gather(*tasks, return_exceptions=True)

    logging.info("Scraping all table pages done!")

    for soup in results:
      page_data = parse_table(soup)
      all_data.extend(page_data)
    return all_data


async def scrape_all_contract_details(contracts):
  # connector = aiohttp.TCPConnector(limit=2)
  async with aiohttp.ClientSession() as session:
    details_tasks = []
    total_contracts = len(contracts)
    logging.info("Preparing to scrape contract details...")
    await asyncio.sleep(5)
    for i, contract in enumerate(contracts):
      logging.debug(
        f"Creating task for contract detail: {contract['URL zákazky']}")
      details_task = asyncio.create_task(
          scrape_contract_details(session, contract, i + 1, total_contracts))
      details_tasks.append(details_task)
      await asyncio.sleep(REQUEST_DELAY)  # important
    await asyncio.gather(*details_tasks, return_exceptions=True)
    logging.info("Scraping details done!")
    return contracts


async def scrape_all_contract_documents(contracts):
  # connector = aiohttp.TCPConnector(limit=2)
  async with aiohttp.ClientSession() as session:
    documents_tasks = []
    total_contracts = len(contracts)
    logging.info("Preparing to scrape contract documents...")
    await asyncio.sleep(5)
    for i, contract in enumerate(contracts):
      logging.debug(
        f"Creating task for contract documents: {contract['URL zákazky']}")
      documents_task = asyncio.create_task(
          scrape_contract_documents(session, contract, i + 1, total_contracts))
      documents_tasks.append(documents_task)
      await asyncio.sleep(REQUEST_DELAY)  # important
    await asyncio.gather(*documents_tasks, return_exceptions=True)
    logging.info("Scraping documents done!")
    return contracts


async def scrape_all_contract_announcements(contracts):
  # connector = aiohttp.TCPConnector(limit=2)
  async with aiohttp.ClientSession() as session:
    announcements_tasks = []
    total_contracts = len(contracts)
    logging.info("Preparing to scrape contract announcements...")
    await asyncio.sleep(5)
    for i, contract in enumerate(contracts):
      logging.debug(
        f"Creating task for contract announcements: {contract['URL zákazky']}")
      announcements_task = asyncio.create_task(
          scrape_contract_announcements(session, contract, i + 1, total_contracts))
      announcements_tasks.append(announcements_task)
      await asyncio.sleep(REQUEST_DELAY)  # important
    await asyncio.gather(*announcements_tasks, return_exceptions=True)
    logging.info("Scraping announcements done!")
    return contracts


async def scrape_contract_details(session, contract, idx, total):
  url = contract["URL zákazky"]
  logging.debug(f"Scraping contract detail: {url}")
  soup = await scrape_page(session, url, ".table.table-info")

  # Pre kontrolu elementov, môžu byť v inom poradí alebo nemusia byť
  expected_keys = {"Dátum vytvorenia", "Dátum poslednej aktualizácie",
                   "Stav zákazky", "CPV zákazky", "Druh zákazky", "Dátum zverejnenia"}
  found_keys = set()

  # TODO: Zákazka je momentálne upravovaná -
  # <strong>Zákazka je momentálne upravovaná</strong> v class="table table-info"
  # alebo iný dôvod - <strong>Čaká sa...</strong>

  # Find all tables with class 'table table-info' and select the second one
  tables_info = soup.find_all('table', class_='table table-info')
  if len(tables_info) < 2:
    logging.error(f"Second table not found in {url}")
    return contract  # Return original if the second table is not found

  table_info = tables_info[1]
  rows = table_info.find_all('tr')
  for row in rows:
    th = row.find('th')
    td = row.find('td')
    if th and td:
      key = th.text.strip().rstrip(':')

      for br in td.find_all('br'):
        br.replace_with('|||')

      # Process only text nodes directly inside the <td> element, ignoring other
      value = ''.join([str(elem).strip()
                      for elem in td.contents if isinstance(elem, str)])
      value = ' '.join(value.split())
      value = value.replace("|||", "\n")
      if key in expected_keys:
        contract[key] = value
        found_keys.add(key)

  missing_keys = expected_keys - found_keys
  if missing_keys:
    logging.warning(f"Missing {missing_keys} for contract: {url}")

  if (idx % 100 == 0 and idx != 0) or idx == total:
    logging.info(f"Completed details for contract {idx} of {total}")
  return contract


async def scrape_contract_documents(session, contract, idx, total):
  documents_url = get_documents_url(contract["URL zákazky"])
  logging.debug(f"Scraping documents for: {documents_url}")
  soup = await scrape_page(session, documents_url, "table#lists-table", True)

  table = soup.find('table', id='lists-table')
  documents_list = []
  if table:
      # Extracting column indices from headers
    headers = {}
    header_cells = table.find('thead').find_all('th')
    for index, header_cell in enumerate(header_cells):
      header_text = header_cell.text.strip()
      headers[header_text] = index

    rows = table.find('tbody').find_all('tr')
    for row in rows:
      cols = row.find_all('td')
      # Ensure that there are enough columns as per the headers, môže byť iné poradie alebo chýbať
      if len(cols) == len(headers):
        druh_dokumentu = cols[headers['Druh dokumentu']].text.strip()
        nazov_dokumentu = cols[headers['Názov dokumentu']].text.strip()
        zverejnenie = cols[headers['Zverejnenie']].text.strip()
        uprava = cols[headers.get(
          'Úprava', -1)].text.strip() if 'Úprava' in headers else 'N/A'

        formatted_string = f"{druh_dokumentu} - {nazov_dokumentu} - {zverejnenie}"
        if uprava != 'N/A':
          formatted_string += f" ({uprava})"
        documents_list.append(formatted_string)

  if not len(documents_list) > 0:
    logging.debug(f"Empty documents for contract {documents_url}")
  else:
    logging.debug(
      f"Adding {len(documents_list)} documents for contract {documents_url}")

  contract['Dokumenty'] = documents_list
  if (idx % 100 == 0 and idx != 0) or idx == total:
    logging.info(f"Completed documents for contract {idx} of {total}")
  return contract


async def scrape_contract_announcements(session, contract, idx, total):
  announcements_url = get_announcements_url(contract["URL zákazky"])
  logging.debug(f"Scraping announcements for: {announcements_url}")
  soup = await scrape_page(session, announcements_url, "table#lists-table", True)

  # Find the table by ID
  table = soup.find('table', id='lists-table')
  announcements_list = []
  if table:
    rows = table.find('tbody').find_all('tr')
    for row in rows:
      cols = row.find_all('td')
      if len(cols) >= 3:
        # Skratka za pomĺčkou, pred br elementom
        for br in cols[0].find_all('br'):
          br.replace_with('|||')

        full_text = cols[0].text.strip()
        shortcut = full_text.split(
          '-')[1].strip().split("|||")[0] if '-' in full_text else 'N/A'

        datum_zverejnenia = cols[1].text.strip()
        # Extracting the URL from the onclick attribute
        announcement_url = "https://www.uvo.gov.sk" + \
            row.get('onclick').split("'")[1]

        # Format: "Skratka - Dátum zverejnenia - URL"
        formatted_string = f"{shortcut} - {datum_zverejnenia} - {announcement_url}"
        announcements_list.append(formatted_string)

  if not len(announcements_list) > 0:
    logging.debug(f"Empty announcements for contract {announcements_url}")
  else:
    logging.debug(
      f"Adding {len(announcements_list)} announcements for contract {announcements_url}")

  contract['Oznámenia'] = announcements_list
  if (idx % 100 == 0 and idx != 0) or idx == total:
    logging.info(f"Completed announcements for contract {idx} of {total}")
  return contract


def get_documents_url(detail_url):
  return detail_url.replace("/detail/", "/dokumenty/")


def get_announcements_url(detail_url):
  return detail_url.replace("/detail/", "/oznamenia/")


def save_to_json(data, filename='data.json'):
  with open(filename, 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
