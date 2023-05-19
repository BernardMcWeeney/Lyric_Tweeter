import json
import requests
import tweepy
import re
from decouple import config
import os

TWITTER_MAX_CHAR = 280
TEST_MODE = True

# Set up Twitter API authentication
bearer_token = config('bearer_token')
consumer_key = config('consumer_key')
consumer_secret = config('consumer_secret')
access_token = config('access_token')
access_token_secret = config('access_token_secret')

client = tweepy.Client(bearer_token,consumer_key,consumer_secret,access_token,access_token_secret)


def save_progress(index_updates):
    progress = load_progress()
    progress.update(index_updates)

    with open('progress.json', 'w') as progress_file:
        json.dump(progress, progress_file)


def load_progress():
    if os.path.exists('progress.json'):
        with open('progress.json', 'r') as progress_file:
            return json.load(progress_file)
    else:
        return {"album_index": 0, "track_index": 0, "tweet_index": 0}


def tweet_lyrics(lyrics_dict, tweet_index, track_index, TEST_MODE):
    
    tweetlist = list(lyrics_dict.items())
    tweet = tweetlist[tweet_index][1]

    #print(tweet_index, len(tweetlist))

    if TEST_MODE:
        print(f"\nTest mode - Tweet {tweet_index+1}: {tweet}")
    else:
        try:
            client.create_tweet(
                text=tweet
            )
            print(f"Tweet {tweet_index+1} sent: {tweet}")
        except Exception as e:
            print(f"Error sending tweet {tweet_index}: {e}")
    
    # update progress
    if tweet_index+1 >= (len(tweetlist)):
        track_index +=1;save_progress({'track_index': track_index})
        tweet_index =0;save_progress({'tweet_index': tweet_index})
    else:
        tweet_index +=1;save_progress({'tweet_index': tweet_index})


def create_lyrics_dict(lyrics):
    lyrics_dict = {}
    tweet_num = 1
    
    # Split lyrics into lines
    lines = lyrics.split('\n')
    
    tweet = ""
    for line in lines:
        if len(tweet) + len(line) + 1 <= TWITTER_MAX_CHAR:  # +1 for the newline character
            tweet += line + '\n'
        else:
            # If adding the current line exceeds TWITTER_MAX_CHAR, save the current tweet and start a new one
            lyrics_dict[tweet_num] = tweet.strip()
            tweet_num += 1
            tweet = line + '\n'
    
    # Add the remaining lyrics, if any
    if tweet.strip():
        lyrics_dict[tweet_num] = tweet.strip()
    
    return lyrics_dict


def upload_album_art(url):
    if TEST_MODE:
        return None
    else:
        response = requests.get(url)
        media = client.media_upload(response.content)
        media_id = media["media_key"]
        return media_id

def get_lyrics(album_index, track_index, tweet_index):
    with open('The_Cure_songs.json', 'r') as file:
        data = json.load(file)

    sorted_albums = sorted(data, key=lambda x: (x['release_date_components']['year'] or float('inf'), x['release_date_components']['month'] or float('inf'), x['release_date_components']['day'] or float('inf')))

    album = sorted_albums[album_index]
    #print(f"Album {album_index}: {album['name']}\n")

    tracklist = album['tracks']
    track = tracklist[track_index]
    
    lyrics = track['song']['lyrics']
    

    # Upload album art only if it's the first song
    #if track_index == 0 & tweet_index == 0:
    #    media_id = upload_album_art(album['cover_art_url'])

    lyrics = re.sub(r'^\d+.*\n', '', lyrics) # Remove the first line that starts with a number
    lyrics = re.sub(r'You might also like\d+Embed', '', lyrics) # Remove the unwanted text from the end of the song using a regular expression
    lyrics = re.sub(r'You might also like', '', lyrics)  # Remove "You might also like"
    lyrics = re.sub(r'39Embed', '', lyrics)  # Remove "39Embed"
    lyrics = re.sub(r'\[.*?\]\n', '', lyrics) # remove [Chorus], [Outro], [Bridge], [Verse 2]
    
    lyrics_to_tweet = create_lyrics_dict(lyrics)
    tweet_lyrics(lyrics_to_tweet, tweet_index, track_index, TEST_MODE)

    #print(track_index,len(album['tracks']))
    # update progress
    if track_index+1 >= (len(album['tracks'])):
        album_index += 1;save_progress({'album_index': album_index})
        track_index =0;save_progress({'track_index': track_index})
        tweet_index =0;save_progress({'tweet_index': tweet_index})


# get the lyrics
loadedprogress = load_progress()
get_lyrics(loadedprogress['album_index'], loadedprogress['track_index'], loadedprogress['tweet_index'])
