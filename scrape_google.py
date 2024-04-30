import signal
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pymongo
import os
import logging
import pandas as pd

class Scraper:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.mongouri = "mongodb://praneeth.chinthalapudi:e4oS9c094MOpL2QDhM2P@23.21.151.206:27017/admin?"
        self.dbname = "ML_DATA_COLL_UI_DATABASE"
        self.collection_name = "meta_scraped_data"
        self.client = pymongo.MongoClient(self.mongouri)
        self.db = self.client[self.dbname]
        self.collection = self.db[self.collection_name]
        self.collection1 = self.db["title_loc"]

    def get_page_content(self, browser, url):
        page = browser.new_page()
        page.goto(url)
        return page.content()

    def extract_description_and_meta(self, content):
        soup = BeautifulSoup(content, features="lxml")
        res = soup.find_all("meta")
        description_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"name": "og:description"})
        description_content = description_tag.get("content") if description_tag else None
        title_tag = soup.find("meta", attrs={"name": "title"}) or soup.find("meta", attrs={"name": "og:title"})
        title_content = title_tag.get("content") if title_tag else None
        meta_content = {meta.get('name'): meta.get('content') for meta in res}
        return description_content, title_content, meta_content

    def get_search_results(self, query):
        results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(args=[
                    "--no-sandbox",
                    "--lang=en-GB,en",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certifcate-errors",
                    "--ignore-certifcate-errors-spki-list"
                ])
                context=browser.new_context()
                page = context.new_page()
                page.goto(f"https://www.google.com/search?q={query}")
                page.wait_for_selector('#rso', timeout=30000)

                div_elements = page.query_selector_all('//div[@class="tF2Cxc"]')[:5]

                for div_element in div_elements:
                    url_element = div_element.query_selector('a')
                    if url_element:
                        url = url_element.get_attribute('href')
                        if 'google.com' not in url:
                            title_element = div_element.query_selector('h3')
                            if title_element:
                                title = title_element.inner_text()
                                content = self.get_page_content(browser, url)
                                description, title_content, meta = self.extract_description_and_meta(content)
                                result_data = {
                                    "Query": query,
                                    "Title": title,
                                    "URL": url,
                                    "Description": description or "",
                                    "Title_Content": title_content or "",
                                    "Meta": str(meta) or None
                                }
                                results.append(result_data)
                context.close()
                browser.close()
        except Exception as e:
            logging.error(f"Error occurred while scraping for query '{query}': {e}")

        df = pd.DataFrame(results)
        print(len(df))
        return df

    def signal_handler(self, signum, frame):
        logging.info("Signal received. Cleaning up and exiting...")
        exit()

    def run_scraper(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        while True:
            row = self.collection1.find_one_and_update({"flag": 0},{"$set": {"flag": 1}})
            if row:
                query = f"{row['title']} near {row['location']}"
                try:
                    df_results = self.get_search_results(query)
                    print(len(df_results))
                    if not df_results.empty:
                        # Convert DataFrame to list of dictionaries and remove None keys
                        records = df_results.apply(lambda x: {k: v for k, v in x.items() if v is not None}, axis=1).to_list()
                        self.collection.insert_many(records)
                        logging.info("Records inserted into MongoDB.")
                    else:
                        logging.warning(f"No results found for query '{query}'. Skipping...")
                except Exception as e:
                    logging.error(f"An error occurred for query '{query}': {e}")
                    logging.warning(f"Skipping query '{query}'.")
            else:
                logging.info("No more rows with flag=0 found in the collection 'title_loc'.")
                break

if __name__ == "__main__":
    scraper = Scraper()
    scraper.run_scraper()
