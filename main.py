import json
import requests
from bs4 import BeautifulSoup

ep_start = str(0)
ep_end = str(5000)
anime_id = str(1500) #1502
default_ep = str(1)

url = "https://www04.gogoanimes.tv/load-list-episode?ep_start="+ep_start+"&ep_end="+ep_end+"&id="+anime_id+"&default_ep="+default_ep

req = requests.get(url)
page = req.text
soup = BeautifulSoup(page, "lxml")
episodes = ["https://www04.gogoanimes.tv"+tag.get("href").strip() for tag in soup.findAll("a")]
print(url)
print(episodes)

print(episodes[-1])

def download_episode(url):
    req = requests.get(url)
    page = req.text
    soup = BeautifulSoup(page, "lxml")
    video_src = "https://"+soup.find("div", attrs={"class": "play-video"}).find("iframe").get("src")[2:]
    print(video_src)
    req = requests.get(video_src)
    page = req.text
    soup = BeautifulSoup(page, "lxml") #5
    js = soup.findAll("script")[4]
    print(js)
    #video_src = "https://"+soup.find("div", attrs={"class": "play-video"}).find("iframe").get("src")[2:]

download_episode(episodes[-1])


