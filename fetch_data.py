import requests
import xmltodict
import sqlite3
import logging
from time import sleep

# --- Setup logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Database connection and setup ---
conn = sqlite3.connect('arxiv_papers.db')
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    title TEXT,
    authors TEXT,
    summary TEXT,
    published TEXT,
    url TEXT
)
''')
conn.commit()

def fetch_arxiv_papers(query, max_results=100, start=0, retries=3):
    base_url = 'http://export.arxiv.org/api/query?'
    url = f'{base_url}search_query=all:{query}&start={start}&max_results={max_results}'
    
    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Requesting papers {start} to {start + max_results} (Attempt {attempt})...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad status
            data = xmltodict.parse(response.text)
            return data
        except requests.RequestException as e:
            logging.warning(f"Request failed: {e}")
            if attempt == retries:
                logging.error(f"Failed after {retries} attempts, skipping this batch.")
                return None
            else:
                sleep(5)  # Wait before retrying

def save_papers_to_db(data):
    if data is None:
        logging.info("No data to save for this batch.")
        return

    entries = data.get('feed', {}).get('entry', [])
    if not entries:
        logging.info("No entries found in the API response.")
        return
    if not isinstance(entries, list):
        entries = [entries]  # single entry case

    new_papers = 0
    for entry in entries:
        try:
            paper_id = entry['id'].split('/abs/')[-1]
            title = entry['title'].replace('\n', ' ').strip()
            # Handle authors field, which can be a dict if single author or list if multiple
            authors_data = entry['author']
            if isinstance(authors_data, list):
                authors = ", ".join(author['name'] for author in authors_data)
            else:
                authors = authors_data['name']
            summary = entry['summary'].replace('\n', ' ').strip()
            published = entry['published']
            url = entry['id']

            cur.execute('''
            INSERT INTO papers (id, title, authors, summary, published, url)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (paper_id, title, authors, summary, published, url))
            new_papers += 1
        except sqlite3.IntegrityError:
            logging.debug(f"Paper {paper_id} already in DB, skipping.")
        except Exception as e:
            logging.error(f"Failed to save paper {paper_id}: {e}")

    conn.commit()
    logging.info(f"Saved {new_papers} new papers to database.")

if __name__ == "__main__":
    query = "machine learning"
    total_to_fetch = 30000
    batch_size = 100

    for start in range(0, total_to_fetch, batch_size):
        data = fetch_arxiv_papers(query, max_results=batch_size, start=start)
        save_papers_to_db(data)
        sleep(3)  # polite delay

    logging.info("Finished fetching and storing papers.")
    conn.close()
