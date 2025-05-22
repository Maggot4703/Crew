import os
import requests
from bs4 import BeautifulSoup
import json

# Define the movie title
movie_title = "Blade Runner"

# Create a folder to save the information
folder_name = f"{movie_title.replace(' ', '_')}_Research"
os.makedirs(folder_name, exist_ok=True)

# Function to get plot summary from Wikipedia
def get_plot_summary(movie_title):
    search_url = f"https://en.wikipedia.org/w/index.php?search={movie_title}&title=Special:Search"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    link = soup.find('a', {'class': 'mw-redirect', 'href': True})
    if link:
        plot_url = f"https://en.wikipedia.org{link['href']}"
        plot_response = requests.get(plot_url)
        plot_soup = BeautifulSoup(plot_response.content, 'html.parser')
        plot_section = plot_soup.find('span', {'id': 'Plot'})
        if plot_section:
            plot_summary = plot_section.find_next('p').get_text()
            return plot_summary
    return "Plot summary not found."

# Function to get character information from Wikipedia
def get_character_info(movie_title):
    search_url = f"https://en.wikipedia.org/w/index.php?search={movie_title}&title=Special:Search"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    link = soup.find('a', {'class': 'mw-redirect', 'href': True})
    if link:
        character_url = f"https://en.wikipedia.org{link['href']}"
        character_response = requests.get(character_url)
        character_soup = BeautifulSoup(character_response.content, 'html.parser')
        character_section = character_soup.find('span', {'id': 'Characters'})
        if character_section:
            character_info = {}
            for char in character_section.find_next('ul').find_all('li'):
                char_name = char.find('a').get_text()
                char_background = char.find_next('p').get_text()
                character_info[char_name] = char_background
            return character_info
    return "Character information not found."

# Function to get images of characters
def get_character_images(movie_title):
    search_url = f"https://www.google.com/search?q={movie_title}+characters&tbm=isch"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    images = []
    for img in soup.find_all('img'):
        img_url = img.get('src')
        if img_url:
            images.append(img_url)
    return images

# Function to get YouTube link to the title song
def get_youtube_link(movie_title):
    search_url = f"https://www.youtube.com/results?search_query={movie_title}+title+song"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    video_link = soup.find('a', {'class': 'yt-simple-endpoint style-scope ytd-video-renderer'})
    if video_link:
        return f"https://www.youtube.com{video_link['href']}"
    return "YouTube link not found."

# Function to create a list of web links
def create_web_links(movie_title):
    search_url = f"https://www.google.com/search?q={movie_title}+science+fiction"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = []
    for link in soup.find_all('a', {'href': True}):
        href = link['href']
        links.append(href)
    return links
