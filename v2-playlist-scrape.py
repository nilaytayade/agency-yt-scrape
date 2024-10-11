import os
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tqdm import tqdm

# Replace with your own API key from the Google Developers Console
YOUTUBE_API_KEY = 'AIzaSyCHfLp3_WhzDV3OKHgPxWJ06e6j-P_D_eE'

# Replace with your own Gemini API Key
GEMINI_API_KEY = 'AIzaSyAfrEIX5ZJ7wk0dt6QiudlaUUxHPN_jz0g'

# Replace with the path to your Google Sheets API credentials file
GOOGLE_SHEETS_CREDENTIALS_FILE = 'creds.json'

def get_youtube_service():
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_playlist_videos(youtube, playlist_id):
    # Get the list of videos from the playlist
    videos = []
    request = youtube.playlistItems().list(
        part='snippet',
        playlistId=playlist_id,
        maxResults=5  # You can increase or paginate for more videos
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

def save_to_google_sheets(data, playlist_id):
    # Define the scope and authenticate with Google Sheets
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS_FILE, scope)
    client = gspread.authorize(credentials)

    # Create a new Google Sheet
    sheet = client.create(f"YouTube Playlist {playlist_id} Videos")

    # Share the sheet to be publicly editable
    sheet.share(None, perm_type='anyone', role='writer')

    # Open the first worksheet
    worksheet = sheet.get_worksheet(0)

    # Set the headers
    headers = ['Title', 'Link', 'Upload Date', 'Video ID', 'Channel Name', 'Channel Link', 'Transcript', 'Summary']
    worksheet.append_row(headers)

    # Append the video data
    for video in data:
        worksheet.append_row([video['title'], video['link'], video['upload_date'], video['video_id'], video['channel_name'], video['channel_link'], video.get('transcript', ''), video.get('summary', '')])

    print(f"Google Sheet created and data saved. Public link: {sheet.url}")

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

    # Fetch transcript and summary for each video with progress indicator
    for video in tqdm(videos, desc="Processing videos", unit="video"):
        video['transcript'] = get_transcript(video['video_id'])
        
        # Only summarize if the transcript is available
        if video['transcript'] != "Transcript not available":
            video['summary'] = summarize_text(video['transcript'])
        else:
            video['summary'] = "Summary not available"

    # Save to Google Sheets with playlist ID
    save_to_google_sheets(videos, playlist_id)

if __name__ == '__main__':
    main()