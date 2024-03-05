import requests
from bs4 import BeautifulSoup
import csv

def scrape_google():
    url = 'https://www.google.com/search?q=warehouse+jobs+near+me'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    search_results = soup.find_all('div', class_='tF2Cxc')

    job_listings = []
    for result in search_results[:3]:  # Limit to the first 3 results
        title = result.find('h3').text
        url = result.find('a')['href']
        job_listings.append({'title': title, 'url': url})

    return job_listings

def save_to_csv(data):
    with open('warehouse_jobs.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title', 'URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for job in data:
            writer.writerow({'Title': job['title'], 'URL': job['url']})

if __name__ == "__main__":
    job_listings = scrape_google()
    save_to_csv(job_listings)
