import os
import requests
from datetime import datetime

YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
WP_URL = "https://tan-gaur-889797.hostingersite.com"
WP_USERNAME = os.environ['WP_USERNAME']
WP_PASSWORD = os.environ['WP_PASSWORD']
ADSENSE_CODE = os.environ.get('ADSENSE_CODE', '')

# YouTube 검색어 → WordPress 카테고리 매핑
CATEGORIES = [
    {'query': 'travel vlog 2025',             'slug': 'travel'},
    {'query': 'k-beauty skincare tutorial',   'slug': 'beauty'},
    {'query': 'AI tools productivity 2025',   'slug': 'ai'},
    {'query': 'trending viral 2025',          'slug': 'trending'},
    {'query': 'lifestyle tips wellness 2025', 'slug': 'lifestyle'},
]


def fetch_youtube_video(query):
    resp = requests.get(
        'https://www.googleapis.com/youtube/v3/search',
        params={
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'order': 'viewCount',
            'maxResults': 1,
            'key': YOUTUBE_API_KEY,
            'relevanceLanguage': 'en',
            'safeSearch': 'moderate',
        },
        timeout=10,
    )
    items = resp.json().get('items', [])
    return items[0] if items else None


def get_wp_category_id(slug):
    resp = requests.get(
        f'{WP_URL}/wp-json/wp/v2/categories',
        params={'slug': slug},
        timeout=10,
    )
    cats = resp.json()
    return cats[0]['id'] if cats else 1


def build_content(video):
    vid_id = video['id']['videoId']
    snippet = video['snippet']
    desc = snippet.get('description', '')[:400]
    channel = snippet.get('channelTitle', '')

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


def post_to_wordpress(title, content, category_id):
    resp = requests.post(
        f'{WP_URL}/wp-json/wp/v2/posts',
        json={
            'title': title,
            'content': content,
            'status': 'publish',
            'categories': [category_id],
        },
        auth=(WP_USERNAME, WP_PASSWORD),
        timeout=15,
    )
    return resp.status_code, resp.json()


def main():
    today = datetime.utcnow().strftime('%Y-%m-%d')
    print(f"[{today}] Starting auto post...")

    for cat in CATEGORIES:
        video = fetch_youtube_video(cat['query'])
        if not video:
            print(f"  {cat['slug']}: no video found, skipping")
            continue

        title = video['snippet']['title']
        content = build_content(video)
        cat_id = get_wp_category_id(cat['slug'])
        status, result = post_to_wordpress(title, content, cat_id)

        if status == 201:
            print(f"  [{cat['slug']}] Posted: {title}")
        else:
            print(f"  [{cat['slug']}] Failed ({status}): {result.get('message', '')}")


if __name__ == '__main__':
    main()
