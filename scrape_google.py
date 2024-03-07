import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import sys

def get_links_from_search_results(query, page):
    page.goto(f"https://www.google.com/search?q={query}")
    page.wait_for_selector("#rso")
    search_results_html = page.content()
    links = [result.find('a').get('href') if result.find('a') else None for result in BeautifulSoup(search_results_html, 'html.parser').select("#rso > div")]
    if links:
        gfj_index = next((i for i, link in enumerate(links) if 'ibp=htl' in link), None)
    else:
        gfj_index = None
    return links if links else [], gfj_index

    
def get_search_results(query, page):
    page.goto(f"https://www.google.com/search?q={query}")
    page.wait_for_selector(".tF2Cxc")
    search_results_html = page.content()
    search_soup = BeautifulSoup(search_results_html, 'html.parser')
    search_results = search_soup.find_all('div', class_='tF2Cxc')[:3]
    job_data = []

    for result in search_results:
        title = result.find('h3').text
        url = result.find('a')['href']
        listing_html = page.content()
        job_data.append((title, url, listing_html))

    return job_data

if __name__ == "__main__":
      
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        df = pd.read_csv("Job_Titles.csv")
        results = []

        for i in range(len(df[1:3])):
            query = df['Title'].iloc[i] + f" jobs near"
            job_data = get_search_results(query, page)
            links,gfj_index = get_links_from_search_results(query, page)
            org_title = df['Title'].iloc[i]
            
            for title, url, listing_html in job_data:
                results.append((org_title, title, url, listing_html, links, gfj_index))

        # Convert the results to a DataFrame
        df_results = pd.DataFrame(results, columns=["Org_Title", "Title", "URL", "Listing_HTML", "Links", "GFJ_Index"])

        # Save the DataFrame as a Parquet file
        df_results.to_parquet("test_results.parquet")

        print("Data extraction complete. Check 'test_results.parquet'")

        context.close()
        browser.close()
