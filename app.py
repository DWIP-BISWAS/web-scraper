import os
from flask import Flask, render_template, request, send_file, redirect, url_for
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json

app = Flask(__name__)

# File to store scraped links for each website
LINKS_FILE = 'scraped_links.json'

def load_scraped_links():
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_scraped_links(links):
    with open(LINKS_FILE, 'w') as f:
        json.dump(links, f)

def get_domain(url):
    return urlparse(url).netloc

def scrape_links(url, max_links):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    time.sleep(2)  # 2-second delay
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Failed to fetch URL: {str(e)}")

    soup = BeautifulSoup(response.text, 'html.parser')
    links = set()
    
    for a_tag in soup.find_all('a', href=True):
        if len(links) >= max_links:
            break
        href = a_tag['href']
        absolute_url = urljoin(url, href)
        links.add(absolute_url)
    
    return sorted(links)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        max_links = int(request.form.get('max_links', 10))
        
        if not url:
            return render_template('index.html', error='Please enter a URL')
        
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = f'http://{url}'
        
        domain = get_domain(url)
        scraped_links = load_scraped_links()
        existing_links = set(scraped_links.get(domain, []))
        
        try:
            new_links = scrape_links(url, max_links)
            unique_links = list(set(new_links) - existing_links)
            
            # Save new links
            scraped_links[domain] = existing_links.union(unique_links)
            save_scraped_links(scraped_links)
            
            # Save new links to a text file for download
            with open('output_links.txt', 'w') as f:
                f.write("\n".join(unique_links))
            
            return redirect(url_for('result', count=len(unique_links), url=url))
        except Exception as e:
            return render_template('index.html', error=f'Error: {str(e)}')
    
    return render_template('index.html')

@app.route('/result')
def result():
    count = request.args.get('count', 0)
    url = request.args.get('url', '')
    return render_template('result.html', count=count, url=url)

@app.route('/download')
def download():
    return send_file('output_links.txt',
                     as_attachment=True,
                     download_name='output_links.txt')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
