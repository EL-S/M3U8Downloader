import json
import requests
from bs4 import BeautifulSoup

path = "data/"

ep_start = str(0)
ep_end = str(5001)
anime_id = str(1501) #1502
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
    global path
    try:
        req = requests.get(url)
        page = req.text
        soup = BeautifulSoup(page, "lxml")
        video_src = "https://"+soup.find("div", attrs={"class": "play-video"}).find("iframe").get("src")[2:]
        print(video_src)
        req = requests.get(video_src)
        headers = {"Origin": "https://vidstreaming.io", "Referer": "https://vidstreaming.io"}
        #print(headers)
        page = req.text
        soup = BeautifulSoup(page, "lxml") #5
        js = soup.findAll("script")[4].text
        m3u8_src = "http://"+js.split("file: '")[1].split("'")[0][8:] #isolate the https link in the js and convert it to http
        print(m3u8_src)
        req = requests.get(m3u8_src, headers=headers)
        m3u8_stream = req.text
        m3u8_stream_doc = m3u8_stream.split("\n")
        #print(m3u8_stream_doc)
        url_domain = "/".join(m3u8_src.split("/")[:-1])+"/"
        print(m3u8_stream_doc[2])
        m3u8_stream_src = url_domain + m3u8_stream_doc[2]
        req = requests.get(m3u8_stream_src, headers=headers)
        m3u8_playlist = req.text
        m3u8_playlist_doc = req.text.split("\n")
        m3u8_links = []
        #print(m3u8_playlist_doc)
        for line in m3u8_playlist_doc:
            try:
                if line[0] != "#":
                    m3u8_links.append(line)
            except:
                pass
        #print(m3u8_links)
        m3u8_src_name = m3u8_src.split("/")[-1:][0]
        with open(path+m3u8_stream_doc[2], "w", encoding="utf-8") as file:
            file.write(m3u8_playlist)
        with open(path+m3u8_src_name, "w", encoding="utf-8") as file:
            file.write(m3u8_stream)
        for sub_link in m3u8_links:
            req = requests.get(url_domain+sub_link, headers=headers)
            m3u8_video_file_part = req.content.decode('latin-1')
            with open(path+sub_link, "w", encoding="latin-1") as file:
                file.write(m3u8_video_file_part)
    except Exception as e:
        print(e)
        download_episode(url)

download_episode(episodes[-1])


#'Expect-CT': 'max-age=604800, report-uri="https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct"', 'Server': 'cloudflare', 'CF-RAY': '476881268bf11914-AKL', 'Content-Encoding': 'gzip'}
