import os
import requests
from bs4 import BeautifulSoup
from tornado import ioloop, httpclient

directory = "Episodes/"
path = ""

#program settings
silent = True

#anime settings
ep_start = str(0)
ep_end = str(5001)
anime_id = str(1502) #1502 watch this one
default_ep = str(1)

#async settings
i = 0
threads = 100

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
    if not silent:
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
    global path
    m3u8_src_name = m3u8_src.split("/")[-1:][0]
    anime_folder(directory+anime_name) #creates the anime folder
    path = directory+anime_name+"/"
    with open(path+m3u8_quality_playlist, "w", encoding="utf-8") as file:
        file.write(m3u8_playlist)
    with open(path+m3u8_src_name, "w", encoding="utf-8") as file:
        file.write(m3u8_stream)
    return path

def download_ts_files(m3u8_links,url_domain,headers,path):
    global i,threads
    http_client = httpclient.AsyncHTTPClient(force_instance=True,defaults=dict(user_agent="Mozilla/5.0"),max_clients=threads)
    for sub_link in m3u8_links:
        url = url_domain+sub_link
        request = httpclient.HTTPRequest(url.strip(),headers=headers,method='GET',connect_timeout=10000,request_timeout=10000)
        http_client.fetch(request,handle_ts_file_response)
        i += 1
    ioloop.IOLoop.instance().start()

def handle_ts_file_response(response):
    if response.code == 599:
        print(response.effective_url,"error")
        http_client.fetch(response.effective_url.strip(), handle_ts_file_response, method='GET',connect_timeout=10000,request_timeout=10000)
    else:
        global i,path
        try:
            file_name = str(response.effective_url.split("/")[-1:][0])
            m3u8_video_file_part = response.body #use binary
            with open(path+file_name, "wb") as file: #save the file as a binary
                file.write(m3u8_video_file_part)
            if not silent:
                print("Downloaded:",file_name)
            #print("alive",response.effective_url)
        except Exception as e:
            print("dead",response.effective_url,e)
        i -= 1
        if i == 0: #all pages loaded
            ioloop.IOLoop.instance().stop()
            print("Download Complete")

def download_episode(url,directory="Episodes/",headers={"Origin": "https://vidstreaming.io", "Referer": "https://vidstreaming.io"}):
    try:
        video_src,anime_name = get_video_src(url)
        if not silent:
            print("Embed Src",video_src)#,anime_name)

        m3u8_src = get_m3u8_initiator_src(video_src)
        if not silent:
            print("M3U8 Src",m3u8_src)

        m3u8_stream_src,url_domain,m3u8_quality_playlist,m3u8_stream = get_m3u8_playlist_src(m3u8_src,headers)
        if not silent:
            print("Playlist:",m3u8_stream_src)#,url_domain)

        m3u8_links,m3u8_playlist = get_m3u8_playlist_links(m3u8_stream_src,headers)
        if not silent:
            print("Parts:",len(m3u8_links))
        
        if not silent:
            print("Saving Playlist Files..")
        path = save_playlist_information(m3u8_src,directory,anime_name,m3u8_quality_playlist,m3u8_playlist,m3u8_stream)

        print("Downloading Episode Files..")
        download_ts_files(m3u8_links,url_domain,headers,path)
        
        print("Finished Episode")
        
    except Exception as e:
        print(e)
        download_episode(episodes[-1],directory)

def download_anime(ep_start,ep_end,anime_id,default_ep):
    url = "https://www04.gogoanimes.tv/load-list-episode?ep_start="+ep_start+"&ep_end="+ep_end+"&id="+anime_id+"&default_ep="+default_ep

    req = requests.get(url)
    page = req.text
    soup = BeautifulSoup(page, "lxml")
    episodes = ["https://www04.gogoanimes.tv"+tag.get("href").strip() for tag in soup.findAll("a")][::-1] #reverses episode order
    if not silent:
        print("API Episodes:",url)
        
    print("Episodes:",len(episodes))

    for episode in episodes:
        print("Episode:",episode)
        download_episode(episode)

init()

download_anime(ep_start,ep_end,anime_id,default_ep)
