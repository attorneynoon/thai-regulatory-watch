"""Probe documented public PDPC WordPress routes from the GitHub runner."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from regwatch.transport import Transport


URLS = [
    'https://www.pdpc.or.th/feed/',
    'https://www.pdpc.or.th/category/pdpc-law/feed/',
    'https://www.pdpc.or.th/category/pdpc-law/announce/feed/',
    'https://www.pdpc.or.th/category/pdpc-news/feed/',
    'https://www.pdpc.or.th/wp-json/wp/v2/posts?per_page=10&_fields=id,date,modified,link,title,excerpt,categories',
    'https://www.pdpc.or.th/wp-json/wp/v2/categories?per_page=100&_fields=id,name,slug,count',
]


def main():
    for url in URLS:
        transport = Transport(['www.pdpc.or.th'])
        try:
            status, headers, body, final = transport.fetch(url)
            print(json.dumps({
                'url': url,
                'status': status,
                'content_type': headers.get('Content-Type'),
                'bytes': len(body),
                'final_url': final,
            }, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(json.dumps({
                'url': url,
                'status': 'blocked-or-failed',
                'error_type': type(exc).__name__,
                'error': str(exc)[:300],
            }, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
