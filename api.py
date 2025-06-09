from flask import Flask, request, jsonify
import cloudscraper
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import socket
import sys
import logging

app = Flask(__name__)

# Configure logging to show warnings and errors, but reduce noise
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

def get_local_ip():
    """Get the machine's local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connect to a public IP to get local IP
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"  # Fallback to default

def get_fdown_download_links(fb_url):
    """
    Scrape FDown.net to get download links and title for a given Facebook video URL.
    
    Args:
        fb_url (str): The Facebook video URL to download.
    
    Returns:
        dict: Contains download links and video title, or error message.
    """
    try:
        base_url = "https://fdown.net/"
        session = cloudscraper.create_scraper()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': base_url,
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1'
        }
        
        # Fetch main page
        response = session.get(base_url, headers=headers, timeout=5)
        response.raise_for_status()
        
        # Submit form to download.php
        form_data = {'URLz': fb_url}
        action_url = urljoin(base_url, "download.php")
        post_response = session.post(action_url, data=form_data, headers=headers, timeout=5)
        post_response.raise_for_status()
        
        # Parse response
        soup = BeautifulSoup(post_response.text, 'html.parser')
        
        # Check for errors
        error_div = soup.find('div', class_='alert-danger')
        if error_div:
            error_text = error_div.get_text(strip=True).lower()
            if "private" in error_text:
                return {"error": "The video is private or restricted. Please use a public video URL."}
            elif "invalid" in error_text or "not found" in error_text:
                return {"error": "The provided URL is invalid or not supported. Ensure it’s a valid Facebook video URL."}
            return {"error": "Unknown error from FDown.net"}
        
        # Extract video title
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            # Fallback to h1 or h2 if title tag is missing
            heading = soup.find(['h1', 'h2'])
            if heading:
                title = heading.get_text(strip=True)
        # Clean up title (remove site branding if present)
        if title and "FDown" in title:
            title = title.replace(" - FDown", "").strip()
        if not title:
            title = "Unknown Title"
        
        # Extract download links
        download_links = []
        sd_link = soup.find('a', id='sdlink')
        hd_link = soup.find('a', id='hdlink')
        
        if sd_link and sd_link.get('href'):
            download_links.append({'quality': 'SD', 'url': sd_link['href']})
        
        if hd_link and hd_link.get('href'):
            download_links.append({'quality': 'HD', 'url': hd_link['href']})
        
        # Fallback: Extract .mp4 links using regex
        if not download_links:
            link_pattern = re.compile(r'(https?://[^\s\'"]+\.mp4[^\'"\s]*)')
            matches = link_pattern.findall(post_response.text)
            for i, link in enumerate(set(matches), 1):
                download_links.append({'quality': f'Quality_{i}', 'url': link})
        
        if not download_links:
            return {"error": "No downloadable video links found."}
        
        return {"links": download_links, "title": title}
    
    except Exception as e:
        return {"error": f"Failed to fetch download links: {str(e)}"}

@app.route('/', methods=['GET'])
def welcome():
    """
    Root endpoint with a basic welcome message.
    """
    return jsonify({
        "status": "success",
        "message": "Welcome to the Facebook Video Downloader API!",
        "endpoint": "/dl?url=<facebook_video_url>",
        "example": "/dl?url=https://www.facebook.com/some-public-video"
    }), 200

@app.route('/dl', methods=['GET'])
def download_links():
    """
    API endpoint to get download links and title for a Facebook video URL.
    
    Query Parameter:
        url: The Facebook video URL (e.g., /dl?url=https://www.facebook.com/video-url)
    
    Response JSON:
        {"links": [{"quality": "HD", "url": "link"}, ...], "title": "Video Title"} or {"error": "message"}
    """
    try:
        fb_url = request.args.get('url', '').strip()
        if not fb_url:
            return jsonify({"error": "Missing 'url' query parameter"}), 400
        
        result = get_fdown_download_links(fb_url)
        if "error" in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    port = 5000
    ip = get_local_ip()
    print(f"Starting Flask server on http://{ip}:{port}/", flush=True)
    try:
        app.run(host="0.0.0.0", port=port, debug=True)  # Re-enable default reloader
    except Exception as e:
        print(f"Failed to start server: {str(e)}", flush=True)
        sys.exit(1)
