import os
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

# Replace with your own API key from the Google Developers Console
YOUTUBE_API_KEY = 'AIzaSyCHfLp3_WhzDV3OKHgPxWJ06e6j-P_D_eE'
YOUTUBE_CHANNEL_ID = 'UCPwZT0o-wVqMFjM8PNoVH7A'

# Replace with your own Gemini API Key
GEMINI_API_KEY = 'AIzaSyAfrEIX5ZJ7wk0dt6QiudlaUUxHPN_jz0g'

def get_youtube_service():
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_channel_info(youtube, channel_id):
    request = youtube.channels().list(
        part="snippet",
        id=channel_id
    )
    response = request.execute()
    
    if 'items' in response:
        return response['items'][0]['snippet']['title']
    return "Unknown Channel"

def get_channel_videos(youtube, channel_id):
    # Get the list of videos from the channel
    videos = []
    request = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        maxResults=5,  # You can increase or paginate for more videos
        type='video',
        order='date'
    )
    response = request.execute()

    for item in response['items']:
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        video_link = f"https://www.youtube.com/watch?v={video_id}"
        upload_date = item['snippet']['publishedAt']
        
        videos.append({
            'title': video_title,
            'link': video_link,
            'upload_date': upload_date,
            'video_id': video_id
        })

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

def save_to_csv(data, channel_name):
    df = pd.DataFrame(data)
    filename = f"{channel_name.replace(' ', '_')}_youtube_videos.csv"
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def main():
    youtube = get_youtube_service()

    # Get channel name
    channel_name = get_channel_info(youtube, YOUTUBE_CHANNEL_ID)

    # Get videos from the specific YouTube channel
    videos = get_channel_videos(youtube, YOUTUBE_CHANNEL_ID)

    # Fetch transcript and summary for each video
    for video in videos:
        video['transcript'] = get_transcript(video['video_id'])
        
        # Only summarize if the transcript is available
        if video['transcript'] != "Transcript not available":
            video['summary'] = summarize_text(video['transcript'])
        else:
            video['summary'] = "Summary not available"

    # Save to CSV with channel name
    save_to_csv(videos, channel_name)

if __name__ == '__main__':
    main()