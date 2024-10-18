from flask import Flask, render_template, request, redirect, url_for
import requests
import hashlib
import os
import time
from bs4 import BeautifulSoup

app = Flask(__name__)

# File to store website content hashes, URLs, and timestamps
HASH_FILE = 'website_hashes.txt'

# Define the user-agent header to mimic a web browser request
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'}

def get_website_content(url):
    try:
        # Fetch website content with headers
        response = requests.get(url, timeout=3, headers=HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove common footer elements
            if soup.footer:
                soup.footer.decompose()
            return soup.get_text()
        else:
            return None
    except Exception as e:
        return None

def hash_content(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def load_hashes():
    # Load the hash data from the file
    hashes = {}
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'r') as f:
            for line in f:
                url, content_hash, last_checked, last_updated = line.strip().split(',')
                hashes[url] = {'hash': content_hash, 'last_checked': last_checked, 'last_updated': last_updated}
    return hashes

def save_hashes(hashes):
    # Save the hash data back to the file
    with open(HASH_FILE, 'w') as f:
        for url, data in hashes.items():
            f.write(f"{url},{data['hash']},{data['last_checked']},{data['last_updated']}\n")

def check_and_update_status():
    # Load the current hashes and timestamps
    hashes = load_hashes()
    statuses = []

    # Check each URL and update the status
    for url, data in hashes.items():
        old_hash = data['hash']
        last_checked = data['last_checked']
        last_updated = data['last_updated']
        content = get_website_content(url)
        current_checked = time.strftime('%Y-%m-%d %H:%M:%S')
        if content:
            current_hash = hash_content(content)
            if current_hash == old_hash:
                statuses.append((url, "Content has not changed", last_checked, current_checked, last_updated, False))
            else:
                # Update the hash and note the content has changed
                current_updated = current_checked  # Last updated is the current check time when the content changes
                hashes[url] = {'hash': current_hash, 'last_checked': current_checked, 'last_updated': current_updated}
                statuses.append((url, "Content has changed", last_checked, current_checked, current_updated, True))
        else:
            statuses.append((url, "Failed to fetch content", last_checked, current_checked, last_updated, False))

    # Save the updated hashes and timestamps
    save_hashes(hashes)

    return statuses

@app.route('/')
def home():
    statuses = check_and_update_status()
    return render_template('index.html', statuses=statuses, time=time)

@app.route('/add_website', methods=['POST'])
def add_website():
    url = request.form.get('url')

    if url:
        # Fetch the content for the first time
        content = get_website_content(url)
        if content:
            current_hash = hash_content(content)
            current_checked = time.strftime('%Y-%m-%d %H:%M:%S')

            # Load existing hashes
            hashes = load_hashes()
            hashes[url] = {'hash': current_hash, 'last_checked': current_checked, 'last_updated': current_checked}  # Set last updated initially to current time

            # Save the new hash and timestamps
            save_hashes(hashes)
        else:
            return render_template('index.html', error="Failed to fetch content from the URL")

    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
