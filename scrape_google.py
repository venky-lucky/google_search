import requests
from bs4 import BeautifulSoup
import csv

def scrape_google(location):
  url = f'https://www.google.com/search?q=warehouse+jobs+{location}'  # Include location in query
  headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
  response = requests.get(url, headers=headers)
  soup = BeautifulSoup(response.text, 'html.parser')
  search_results = soup.find_all('div', class_='tF2Cxc')

  job_listings = []
  for result in search_results[:3]:  # Limit to the first 3 results
    title = result.find('h3').text
    url = result.find('a')['href']

    # Fetch the job listing page content
    listing_response = requests.get(url, headers=headers)
    listing_soup = BeautifulSoup(listing_response.text, 'html.parser')
    # Assuming the job description is in a specific element (replace with the actual selector)
    job_description = listing_soup.find('div', class_='job-description').text  # Modify this selector based on the website's structure

    job_listings.append({'title': title, 'url': url, 'html': job_description})

  return job_listings

if __name__ == "__main__":
  location = 'US'  # Placeholder, can be passed as an argument
  job_listings = scrape_google(location)
  with open('output/warehouse_jobs.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Title', 'URL', 'HTML']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for job in job_listings:
      writer.writerow(job)
