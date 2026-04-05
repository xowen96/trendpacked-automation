import os
import requests
from datetime import datetime, timezone

YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
WP_URL = "https://trendpacked.com"
WP_API_TOKEN = os.environ['WP_API_TOKEN']
ADSENSE_CODE = os.environ.get('ADSENSE_CODE', '')

CATEGORIES = [
    {'query': 'travel vlog 2025 best destination',  'slug': 'travel'},
    {'query': 'k-beauty skincare routine tutorial', 'slug': 'beauty'},
    {'query': 'AI tools productivity 2025',         'slug': 'ai'},
    {'query': 'trending viral youtube 2025',        'slug': 'trending'},
    {'query': 'lifestyle tips wellness 2025',       'slug': 'lifestyle'},
]

# Affiliate links per category (update YOUR_*_AFF_ID with actual IDs)
AFFILIATE = {
    'travel': [
        ('🏨 Best Hotels on Booking.com', 'https://www.booking.com/'),
        ('🎟 Tours & Activities on Klook', 'https://www.klook.com/en-US/'),
    ],
    'beauty': [
        ('🛍 Shop K-Beauty on YesStyle', 'https://www.yesstyle.com/'),
        ('📦 K-Beauty on Amazon', 'https://www.amazon.com/s?k=k-beauty'),
    ],
    'ai': [
        ('📦 Top AI Gadgets on Amazon', 'https://www.amazon.com/s?k=ai+productivity+tools'),
    ],
    'trending': [
        ('🏨 Travel Deals on Booking.com', 'https://www.booking.com/'),
    ],
    'lifestyle': [
        ('🎟 Experiences on Klook', 'https://www.klook.com/en-US/'),
        ('📦 Lifestyle Picks on Amazon', 'https://www.amazon.com/s?k=lifestyle+essentials'),
    ],
}

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


def build_affiliate_block(slug):
    links = AFFILIATE.get(slug, [])
    if not links:
        return ''
    items = ''.join(
        f'<a href="{url}" target="_blank" rel="noopener nofollow" '
        f'style="display:inline-block;background:#1a1a1a;color:#fff;padding:10px 16px;'
        f'border-radius:5px;text-decoration:none;font-size:13px;font-weight:600;'
        f'margin:4px;border:1px solid #333;">{label}</a>'
        for label, url in links
    )
    return f"""
<!-- wp:html -->
<div style="background:#111;border:1px solid #222;border-radius:8px;padding:16px;margin:24px 0;">
  <p style="color:#e91e8c;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:0 0 10px;">
    🔗 Recommended Deals
  </p>
  {items}
</div>
<!-- /wp:html -->
"""


def build_content(video, cat_slug=''):
    vid_id = video['id']['videoId']
    desc = video['snippet'].get('description', '')[:400]
    channel = video['snippet'].get('channelTitle', '')
    ad_block = f'\n<!-- wp:html -->\n{ADSENSE_CODE}\n<!-- /wp:html -->\n' if ADSENSE_CODE else ''
    aff_block = build_affiliate_block(cat_slug)

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
{aff_block}{ad_block}"""


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
        content = build_content(video, cat['slug'])
        cat_id = get_category_id(cat['slug'])
        thumb_url = f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
        status, result = post_to_wordpress(title, content, cat_id, thumb_url)

        if status == 200:
            print(f"  [{cat['slug']}] Posted: {title[:60]}")
        else:
            print(f"  [{cat['slug']}] Failed ({status}): {result.get('message', result)}")


if __name__ == '__main__':
    main()
