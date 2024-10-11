import os
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

# Replace with your own API key from the Google Developers Console
YOUTUBE_API_KEY = 'AIzaSyCHfLp3_WhzDV3OKHgPxWJ06e6j-P_D_eE'

# Replace with your own Gemini API Key
GEMINI_API_KEY = 'AIzaSyAfrEIX5ZJ7wk0dt6QiudlaUUxHPN_jz0g'

def get_youtube_service():
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_playlist_videos(youtube, playlist_id):
    # Get the list of videos from the playlist
    videos = []
    request = youtube.playlistItems().list(
        part='snippet',
        playlistId=playlist_id,
        maxResults=50 # You can increase or paginate for more videos
    )
    while request:
        response = request.execute()
        for item in response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            video_title = item['snippet']['title']
            video_link = f"https://www.youtube.com/watch?v={video_id}"
            upload_date = item['snippet']['publishedAt']
            channel_title = item['snippet']['channelTitle']
            channel_link = f"https://www.youtube.com/channel/{item['snippet']['channelId']}"

            videos.append({
                'title': video_title,
                'link': video_link,
                'upload_date': upload_date,
                'video_id': video_id,
                'channel_name': channel_title,
                'channel_link': channel_link
            })

        request = youtube.playlistItems().list_next(request, response)

    return videos

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = ' '.join([item['text'] for item in transcript])
        return transcript_text
    except Exception as e:
        return "Transcript not available"

def summarize_text(text):
    # Configure the Gemini API
    genai.configure(api_key=GEMINI_API_KEY)

    # Set up the model
    model = genai.GenerativeModel('gemini-pro')

    try:
        # Generate content
        response = model.generate_content(f"Summarize the following text in this example format=>hook + set frame w/ case studies & results in the first 30s // lay out promise of what the video is going to show // provide proof that this works (goes hand-in-hand w/ frame setting) // clear CTA // we are in a trust recession // interpersonal trust is at an all time low // what worked in 2018 won't work anymore and you will just bleed money // you can no longer rely on *just* cold outreach or paid ads to get quality clients (include references to biggest names in the space and how they are prioritising organic) // paid aids + cold outreach are just initial attention capture // you need to actually educate that attention at scale before even pitching or trying to close // the only way to do that at scale is long form organic on youtube // evergreen platform, 24/7 sales person // handles objection, presells // lowers CPA, increases conversion rates, provides exponentially boosted returns to other acq. channels // but in order to get it right, every single piece needs to be dialled in // from messaging to positioning to consistency (this needs a content ideation system) to knowing how to rank for the right terms to knowing which metrics to track // *only when* all of these are in place can you have a sale smachine that lands presold, qualified warm calls ready to close // transition to overview of how this complements other acq. channels // transition to offer pitch + CTA // end:\n\n{text}")
        
        # Check if the response has text
        if response.text:
            return response.text.strip()
        else:
            return "Summary not available"
    except Exception as e:
        print(f"Error in summarization: {e}")
        return "Summary not available"

def save_to_csv(data, playlist_id):
    df = pd.DataFrame(data)
    filename = f"{playlist_id}_youtube_videos.csv"
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def main():
    youtube = get_youtube_service()

    # Accept playlist link from the user
    playlist_link = input("Enter YouTube playlist link: ")
    playlist_id_match = re.search(r'list=([a-zA-Z0-9_-]+)', playlist_link)
    if not playlist_id_match:
        print("Invalid playlist link.")
        return

    playlist_id = playlist_id_match.group(1)

    # Get videos from the playlist
    videos = get_playlist_videos(youtube, playlist_id)

    # Fetch transcript and summary for each video
    for video in videos:
        video['transcript'] = get_transcript(video['video_id'])
        
        # Only summarize if the transcript is available
        if video['transcript'] != "Transcript not available":
            video['summary'] = summarize_text(video['transcript'])
        else:
            video['summary'] = "Summary not available"

    # Save to CSV with playlist ID
    save_to_csv(videos, playlist_id)

if __name__ == '__main__':
    main()