from googleapiclient.discovery import build
from app.config import settings
from typing import List, Optional

async def search_videos(question: str, subject: Optional[str] = None) -> List[dict]:
    """
    Search for educational videos on YouTube
    """
    try:
        youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
        
        # Build search query
        search_query = f"{question} tutorial explanation"
        if subject:
            search_query += f" {subject}"
        
        # Search YouTube
        request = youtube.search().list(
            q=search_query,
            part='snippet',
            type='video',
            maxResults=3,
            videoCategoryId='27',  # Education category
            relevanceLanguage='en'
        )
        
        response = request.execute()
        
        # Format results
        videos = []
        for item in response.get('items', []):
            videos.append({
                'title': item['snippet']['title'],
                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                'thumbnail': item['snippet']['thumbnails']['medium']['url']
            })
        
        return videos if videos else None
        
    except Exception as e:
        print(f"Video search error: {e}")
        return None