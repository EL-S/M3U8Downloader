import os
import json
import requests
from bs4 import BeautifulSoup

directory = "Episodes/"

ep_start = str(0)
ep_end = str(5001)
anime_id = str(1502) #1502 watch this one
default_ep = str(1)

url = "https://www04.gogoanimes.tv/load-list-episode?ep_start="+ep_start+"&ep_end="+ep_end+"&id="+anime_id+"&default_ep="+default_ep

req = requests.get(url)
page = req.text
soup = BeautifulSoup(page, "lxml")
episodes = ["https://www04.gogoanimes.tv"+tag.get("href").strip() for tag in soup.findAll("a")]
print("API Episodes:",url)
print("Episodes:",len(episodes))

print("Episode Link:",episodes[-1])

def init():
    global directory
    try:
        os.stat(directory)
    except:
        os.mkdir(directory)

def anime_folder(title):
    try:
        os.stat(title)
    except:
        os.mkdir(title)

def get_video_src(url):
    req = requests.get(url)
    page = req.text
    soup = BeautifulSoup(page, "lxml")
    anime_name = soup.find("div", attrs={"class": "title_name"}).find("h2").text
    print("Episode Name:",anime_name)
    #video_src = "https://"+soup.find("div", attrs={"class": "play-video"}).find("iframe").get("src")[2:]
    video_src = soup.find("li", attrs={"class": "vidcdn"}).find("a").get("data-video")
    return video_src,anime_name

def get_m3u8_initiator_src(video_src):
    req = requests.get(video_src)
    page = req.text
    soup = BeautifulSoup(page, "lxml")
    js = soup.findAll("script")[3].text #sometimes [4].text
    m3u8_src = "http://"+js.split("file: '")[1].split("'")[0][8:] #isolate the https link in the js and convert it to http
    return m3u8_src

def get_m3u8_playlist_src(m3u8_src,headers):
    req = requests.get(m3u8_src, headers=headers)
    m3u8_stream = req.text
    m3u8_stream_array = m3u8_stream.split("\n")
    m3u8_stream_options = []
    for line in m3u8_stream_array:
        try:
            if line[0] != "#":
                m3u8_stream_options.append(line)
        except:
            pass
    print("Options:",m3u8_stream_options)
    m3u8_quality_playlist = m3u8_stream_options[0]
    url_domain = "/".join(m3u8_src.split("/")[:-1])+"/"
    m3u8_stream_src = url_domain + m3u8_quality_playlist
    return m3u8_stream_src,url_domain,m3u8_quality_playlist,m3u8_stream

def get_m3u8_playlist_links(m3u8_stream_src,headers):
    req = requests.get(m3u8_stream_src, headers=headers)
    m3u8_playlist = req.text
    m3u8_playlist_doc = req.text.split("\n")
    m3u8_links = []
    for line in m3u8_playlist_doc:
        try:
            if line[0] != "#":
                m3u8_links.append(line)
        except:
            pass
    return m3u8_links,m3u8_playlist

def save_playlist_information(m3u8_src,directory,anime_name,m3u8_quality_playlist,m3u8_playlist,m3u8_stream):
    m3u8_src_name = m3u8_src.split("/")[-1:][0]
    anime_folder(directory+anime_name) #creates the anime folder
    path = directory+anime_name+"/"
    with open(path+m3u8_quality_playlist, "w", encoding="utf-8") as file:
        file.write(m3u8_playlist)
    with open(path+m3u8_src_name, "w", encoding="utf-8") as file:
        file.write(m3u8_stream)
    return path

def download_ts_files(m3u8_links,url_domain,headers,path):
    for sub_link in m3u8_links:
        #do async tornado download here
        req = requests.get(url_domain+sub_link, headers=headers)
        m3u8_video_file_part = req.content #use binary
        with open(path+sub_link, "wb") as file: #save the file as a binary
            file.write(m3u8_video_file_part)
        print("Downloaded:",sub_link)

def download_episode(url,directory="Episodes/",headers={"Origin": "https://vidstreaming.io", "Referer": "https://vidstreaming.io"}):
    try:
        video_src,anime_name = get_video_src(url)
        print("Embed Src",video_src)#,anime_name)

        m3u8_src = get_m3u8_initiator_src(video_src)
        print("M3U8 Src",m3u8_src)

        m3u8_stream_src,url_domain,m3u8_quality_playlist,m3u8_stream = get_m3u8_playlist_src(m3u8_src,headers)
        print("Playlist:",m3u8_stream_src)#,url_domain)

        m3u8_links,m3u8_playlist = get_m3u8_playlist_links(m3u8_stream_src,headers)
        print("Parts:",len(m3u8_links))
        
        print("Saving Playlist Files..")
        path = save_playlist_information(m3u8_src,directory,anime_name,m3u8_quality_playlist,m3u8_playlist,m3u8_stream)

        print("Downloading Playlist Files..")
        download_ts_files(m3u8_links,url_domain,headers,path)
        
        print("Complete")
        
    except Exception as e:
        print(e)
        download_episode(episodes[-1],directory)

init()
download_episode(episodes[-1],directory)


#'Expect-CT': 'max-age=604800, report-uri="https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct"', 'Server': 'cloudflare', 'CF-RAY': '476881268bf11914-AKL', 'Content-Encoding': 'gzip'}
