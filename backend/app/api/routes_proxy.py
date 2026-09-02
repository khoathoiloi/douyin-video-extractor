import aiohttp
from fastapi import APIRouter, Query, Response
from fastapi.responses import Response

router = APIRouter(prefix="/v1")

DEFAULT_SVG_PLACEHOLDER = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <linearGradient id="btn" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fe2c55"/>
      <stop offset="100%" stop-color="#25f4ee"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" fill="url(#bg)"/>
  <circle cx="160" cy="80" r="30" fill="url(#btn)" opacity="0.85"/>
  <polygon points="152,68 174,80 152,92" fill="#ffffff"/>
  <text x="160" y="135" fill="#94a3b8" font-size="12" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" text-anchor="middle" font-weight="600">Douyin Video Cover</text>
  <text x="160" y="152" fill="#64748b" font-size="10" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" text-anchor="middle">Click to view on Douyin</text>
</svg>"""

@router.get("/placeholder/cover.svg")
def get_cover_placeholder():
    return Response(
        content=DEFAULT_SVG_PLACEHOLDER,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@router.get("/proxy/thumbnail")
async def proxy_douyin_thumbnail(url: str = Query(..., description="Target Douyin thumbnail URL")):
    if not url or not url.startswith("http"):
        return Response(content=DEFAULT_SVG_PLACEHOLDER, media_type="image/svg+xml")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }

    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    content_type = resp.headers.get("Content-Type", "image/jpeg")
                    return Response(
                        content=content,
                        media_type=content_type,
                        headers={"Cache-Control": "public, max-age=3600"}
                    )
    except Exception:
        pass

    # Fallback to SVG placeholder on failure
    return Response(
        content=DEFAULT_SVG_PLACEHOLDER,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=3600"}
    )
