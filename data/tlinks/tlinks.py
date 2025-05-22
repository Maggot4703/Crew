#!/usr/bin/python
import subprocess
import webbrowser

# Define the lists of URLs and other data
tmap = ["https://travellermap.com/"]
trpg = ["https://www.travellerrpg.com/"]
comics = ["https://www.comicartfans.com/"]
wikis = ["https://wikipedia.org/"]
SITES = [tmap, trpg, comics, wikis]

worlds = ["Regina", "Roup", "Feri", "Boughene", "Efate", "Lysen", "JUMP"]
ships = ["SkyRig"]
chars = ["PC", "Andii"]
STORY = [worlds, ships, chars]

ALL = [SITES, STORY]


# Function to open URLs in Firefox
def open_urls(urls):
    for url in urls:
#        webbrowser.get('firefox').open(url)

# Open the Traveller Map URL
#webbrowser.get('firefox').open(tmap)




# Function to navigate to specific pages based on the lists
def navigate_to_pages():
    for world in worlds:
        # Construct the URL for each world (example: https://travellermap.com/Regina)
        url = f"https://travellermap.com/{world}"
        webbrowser.get('firefox').open(url)
# Navigate to the pages for each world
#navigate_to_pages()



#openList(lnk:str) -> List:
#
# Define the command to be executed
#command = ["firefox", tmap[0]]
#
# Execute the command
#try:
#    result = subprocess.run(command, check=True, capture_output=True, text=True)
#    # Print the output
#    print("Output:", result.stdout)
#    print("Error (if any):", result.stderr)
#except subprocess.CalledProcessError as e:
#    print(f"Command failed with return code {e.returncode}")
#    print("Error output:", e.stderr)

