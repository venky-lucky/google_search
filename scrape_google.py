import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from tqdm import tqdm

def get_links_from_search_results(query, page):
    page.goto(f"https://www.google.com/search?q={query}")
    page.wait_for_selector("#rso")
    search_results_html = page.content()
    links = [result.find('a').get('href') if result.find('a') else None for result in BeautifulSoup(search_results_html, 'html.parser').select("#rso > div")]
    return links

def get_location(query, page):
    page.goto(f"https://www.google.com/search?q={query}")
    text_locator = page.locator("//span[@class=\"dfB0uf\"]")
    try:
        location = text_locator.inner_text()
    except Exception as e:
        print(f"Error getting location for query '{query}': {e}")
        location = 'Unknown'
    return location

def get_search_results(query, page, location):
    page.goto(f"https://www.google.com/search?q={query}")
    page.wait_for_selector(".tF2Cxc")

    search_results_html = page.content()
    search_soup = BeautifulSoup(search_results_html, 'html.parser')
    search_results = search_soup.find_all('div', class_='tF2Cxc')[:3]

    job_data = []
    for result in search_results:
        title = result.find('h3').text
        url = result.find('a')['href']
        listing_html = result.prettify()
        job_data.append((title, url, location, listing_html))
    
    return job_data

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        df = pd.read_csv("Job_Titles.csv")
        results = []

        for query in tqdm(df['Title'].sample(3), desc="Processing rows", unit="row"):
            try:
                query += " jobs near me"
                location = get_location(query, page)
                job_data = get_search_results(query, page, location)
                links = get_links_from_search_results(query, page)
                gfj_index = None
                if links is not None:
                    for i, s in enumerate(links):
                        if s is not None and 'ibp=htl' in s:
                            gfj_index = i+1
                            break
                for title, url, location, listing_html in job_data:
                    results.append((query, title, url, location, listing_html, links, gfj_index))
            except Exception as e:
                print(f"Exception occurred for query '{query}': {e}")

        df_results = pd.DataFrame(results, columns=["Query", "Title", "URL", "Location", "Listing_HTML", "Links","GFJ_Index"])
        df_results.to_parquet("test_results.parquet")
        print("Data extraction complete. Check 'test_results.parquet'")
        context.close()
        browser.close()
