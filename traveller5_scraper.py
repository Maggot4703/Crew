#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import json
from time import sleep
import re
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime

class Traveller5Scraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.visited_urls = set()
        self.results = []
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            filename=f'traveller5_scraping_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def search_google(self, query, num_results=100):
        base_url = "https://www.google.com/search"
        results = []
        
        for i in range(0, num_results, 10):
            params = {
                'q': query,
                'start': i,
                'num': 10
            }
            
            try:
                response = requests.get(base_url, params=params, headers=self.headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    search_results = soup.find_all('div', class_='g')
                    
                    for result in search_results:
                        link = result.find('a')
                        if link and 'href' in link.attrs:
                            url = link['href']
                            if url.startswith('http'):
                                results.append(url)
                
                sleep(2)  # Respect rate limits
            except Exception as e:
                logging.error(f"Error during Google search: {str(e)}")
        
        return results

    def is_relevant_url(self, url):
        relevant_keywords = ['traveller', 'traveller5', 't5', 'rpg', 'game', 'role-playing']
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in relevant_keywords)

    def scrape_page(self, url):
        if url in self.visited_urls:
            return []
        
        self.visited_urls.add(url)
        links = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                page_links = soup.find_all('a', href=True)
                
                for link in page_links:
                    href = link['href']
                    full_url = urljoin(url, href)
                    
                    if self.is_relevant_url(full_url):
                        links.append({
                            'url': full_url,
                            'text': link.get_text().strip(),
                            'source': url
                        })
            
            sleep(1)  # Respect rate limits
        except Exception as e:
            logging.error(f"Error scraping {url}: {str(e)}")
        
        return links

    def save_results(self, filename='traveller5_links.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        logging.info(f"Results saved to {filename}")

    def run(self):
        # Initial search queries
        queries = [
            'Traveller 5 RPG official site',
            'Traveller 5 RPG resources',
            'Traveller 5 gaming materials',
            'T5 RPG community'
        ]
        
        for query in queries:
            initial_urls = self.search_google(query)
            logging.info(f"Found {len(initial_urls)} initial URLs for query: {query}")
            
            for url in initial_urls:
                if url not in self.visited_urls:
                    links = self.scrape_page(url)
                    self.results.extend(links)
        
        # Remove duplicates and sort by URL
        unique_results = {json.dumps(d, sort_keys=True): d for d in self.results}.values()
        self.results = sorted(unique_results, key=lambda x: x['url'])
        
        self.save_results()
        logging.info(f"Scraping completed. Found {len(self.results)} unique relevant links.")

if __name__ == '__main__':
    scraper = Traveller5Scraper()
    scraper.run()