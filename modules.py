import requests
import sqlite3
from datetime import datetime

DB_NAME = 'app.db'

def connect_to_db():
    return sqlite3.connect(DB_NAME)

# Функция для установления соединения с базой данных
def connect_to_db():
    return sqlite3.connect(DB_NAME)

def youtube_search(chat_id, request):
    connection = connect_to_db()
    cursor = connection.cursor()

    video_search = request
    number_lines = 50

    res = requests.get(
        "https://www.googleapis.com/youtube/v3/search?",
        params={
            'part': 'snippet',
            "q": video_search,
            "maxResults": number_lines,
            "key": "YOUTUBE_API_KEY"
        }
    )

    data = res.json()
    videos = []

    for search_result in data.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            videos.append(
                f"https://www.youtube.com/watch?v={search_result['id']['videoId']}"
            )

    video_links = [(chat_id, video) for video in videos]

    cursor.executemany("INSERT INTO SearchResult (UserId, Link) VALUES (?, ?)", video_links)

    connection.commit()
    connection.close()

    return len(videos)


def search_list(request):
    video_search = request
    number_lines = 50

    res = requests.get(
        "https://www.googleapis.com/youtube/v3/search?",
        params={
            'part': 'snippet',
            "q": video_search,
            "maxResults": number_lines,
            "type": "video,channel,playlist",
            "key": "YOUTUBE_API_KEY"
        }
    )

    data = res.json()

    videos = []
    channels = []
    playlists = []

    for search_result in data.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            videos.append(
                f"{search_result['snippet']['title']}\nhttps://www.youtube.com/watch?v={search_result['id']['videoId']}\n"
            )
        elif search_result["id"]["kind"] == "youtube#channel":
            channels.append(
                f"{search_result['snippet']['title']}\nhttps://www.youtube.com/channel/{search_result['id']['channelId']}"
            )
        elif search_result["id"]["kind"] == "youtube#playlist":
            playlists.append(
                f"{search_result['snippet']['title']}\nhttps://www.youtube.com/playlist?list={search_result['id']['playlistId']}"
            )

    result_text = ""
    if videos:
        result_text += "Videos:\n" + "\n".join(videos) + "\n"
    if channels:
        result_text += "Channels:\n" + "\n".join(channels) + "\n"
    if playlists:
        result_text += "Playlists:\n" + "\n".join(playlists) + "\n"

    return result_text

