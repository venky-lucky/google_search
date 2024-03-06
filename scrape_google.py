import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pickle

def get_links_from_search_results(query):
    driver = webdriver.Chrome()  
    search_url = f"https://www.google.com/search?q={query}"

    try:
        driver.get(search_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#rso")))
        search_results_html = driver.page_source
        links = [result.find('a').get('href') if result.find('a') else None for result in BeautifulSoup(search_results_html, 'html.parser').select("#rso > div")]
    finally:
        driver.quit()
    return links
    
def get_search_results(query, pages):
    driver = webdriver.Chrome()  
    search_url = f"https://www.google.com/search?q={query}"
    job_data = []

    try:
        driver.get(search_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tF2Cxc")))
        search_results_html = driver.page_source
        search_soup = BeautifulSoup(search_results_html, 'html.parser')
        search_results = search_soup.find_all('div', class_='tF2Cxc')[:3]

        for result in search_results:
            title = result.find('h3').text
            url = result.find('a')['href']
            listing_html = driver.page_source
            job_data.append((title, url, listing_html))

    finally:
        driver.quit()

    return job_data

if __name__ == "__main__":
    df = pd.read_csv("Job_Titles.csv")
    results = []

    for i in range(len(df[1:3])):
        query = df['Title'].iloc[i] + " jobs near me"
        job_data = get_search_results(query, 1)
        links = get_links_from_search_results(query)
        org_title = df['Title'].iloc[i]
        gfj_index = None if links is None else next((i for i, link in enumerate(links) if 'ibp=htl' in link), None)
        if gfj_index != None:
            gfj_index+=1
        for title, url, listing_html in job_data:
            results.append((org_title, title, url, listing_html, links, gfj_index))

    with open('test_results.pickle', 'wb') as f:
        pickle.dump(results, f)

