import os
import requests
from datetime import datetime, timezone

YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
WP_URL = "https://tan-gaur-889797.hostingersite.com"
WP_API_TOKEN = os.environ['WP_API_TOKEN']
ADSENSE_CODE = os.environ.get('ADSENSE_CODE', '')

CATEGORIES = [
    {'query': 'travel vlog 2025',             'slug': 'travel'},
    {'query': 'k-beauty skincare tutorial',   'slug': 'beauty'},
    {'query': 'AI tools productivity 2025',   'slug': 'ai'},
    {'query': 'trending viral 2025',          'slug': 'trending'},
    {'query': 'lifestyle tips wellness 2025', 'slug': 'lifestyle'},
]

HEADERS = {'X-TP-Token': WP_API_TOKEN}


def fetch_youtube_video(query):
    resp = requests.get(
        'https://www.googleapis.com/youtube/v3/search',
        params={
            'part': 'snippet', 'q': query, 'type': 'video',
            'order': 'viewCount', 'maxResults': 1,
            'key': YOUTUBE_API_KEY, 'relevanceLanguage': 'en', 'safeSearch': 'moderate',
        },
        timeout=10,
    )
    items = resp.json().get('items', [])
    return items[0] if items else None


def get_category_id(slug):
    resp = requests.get(
        f'{WP_URL}/wp-json/trendpacked/v1/category',
        params={'slug': slug}, timeout=10,
    )
    return resp.json().get('id', 1)


def build_content(video):
    vid_id = video['id']['videoId']
    desc = video['snippet'].get('description', '')[:400]
    channel = video['snippet'].get('channelTitle', '')
    ad_block = f'\n<!-- wp:html -->\n{ADSENSE_CODE}\n<!-- /wp:html -->\n' if ADSENSE_CODE else ''

    return f"""<!-- wp:paragraph -->
<p>{desc}</p>
<!-- /wp:paragraph -->

<!-- wp:html -->
<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;margin:20px 0;">
  <iframe src="https://www.youtube.com/embed/{vid_id}"
    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
    allowfullscreen loading="lazy"></iframe>
</div>
<!-- /wp:html -->

<!-- wp:paragraph -->
<p><em>Source: {channel}</em></p>
<!-- /wp:paragraph -->
{ad_block}"""


def post_to_wordpress(title, content, category_id, thumbnail_url=None):
    data = {
        'title': title,
        'content': content,
        'category_id': category_id,
        'thumbnail_url': thumbnail_url,
    }
    resp = requests.post(
        f'{WP_URL}/wp-json/trendpacked/v1/post',
        json=data, headers=HEADERS, timeout=30,
    )
    return resp.status_code, resp.json()


def main():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    print(f"[{today}] Starting auto post...")

    for cat in CATEGORIES:
        video = fetch_youtube_video(cat['query'])
        if not video:
            print(f"  [{cat['slug']}] no video found")
            continue

        vid_id = video['id']['videoId']
        title = video['snippet']['title']
        content = build_content(video)
        cat_id = get_category_id(cat['slug'])
        thumb_url = f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
        status, result = post_to_wordpress(title, content, cat_id, thumb_url)

        if status == 200:
            print(f"  [{cat['slug']}] Posted: {title[:60]}")
        else:
            print(f"  [{cat['slug']}] Failed ({status}): {result.get('message', result)}")


if __name__ == '__main__':
    main()
