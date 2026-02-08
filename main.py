import aiohttp
import asyncio
from bs4 import BeautifulSoup
import time

from config import *

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

sent_links = set()

def jpy_to_pln(jpy):
    return round(jpy * JPY_TO_PLN, 2)

async def send_to_discord(item):
    embed = {
        "title": item["title"],
        "url": item["url"],
        "color": 0xC00000,
        "fields": [
            {"name": "💴 Cena", "value": f'{item["price_pln"]} zł', "inline": True},
            {"name": "📏 Rozmiar", "value": item["size"], "inline": True},
            {"name": "🇯🇵 Źródło", "value": item["site"], "inline": True}
        ],
        "image": {"url": item["image"]},
        "footer": {"text": "Japan Second‑Hand Monitor"}
    }

    async with aiohttp.ClientSession() as session:
        await session.post(WEBHOOK_URL, json={"embeds": [embed]})

async def search_mercari(keyword):
    url = f"https://www.mercari.com/jp/search/?keyword={keyword}"
    results = []

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as r:
            soup = BeautifulSoup(await r.text(), "html.parser")

            for item in soup.select("a"):
                try:
                    title = item.text.strip()
                    if not title:
                        continue

                    link = "https://www.mercari.com" + item.get("href", "")
                    if link in sent_links:
                        continue

                    price_text = item.text
                    if "¥" not in price_text:
                        continue

                    price_jpy = int(price_text.split("¥")[-1].replace(",", "").strip())
                    price_pln = jpy_to_pln(price_jpy)

                    if price_pln > MAX_PRICE_PLN:
                        continue

                    img = item.find("img")
                    img_url = img["src"] if img else None

                    size = "?"
                    for s in JP_SIZES:
                        if s in title:
                            size = s

                    results.append({
                        "title": title[:250],
                        "price_pln": price_pln,
                        "url": link,
                        "image": img_url,
                        "site": "Mercari JP",
                        "size": size
                    })

                    sent_links.add(link)

                except:
                    continue

    return results

async def main_loop():
    while True:
        print("🔍 Sprawdzam...")
        for keyword in KEYWORDS:
            items = await search_mercari(keyword)
            for item in items:
                await send_to_discord(item)
                await asyncio.sleep(1)

        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    
    # Testujemy webhook
    asyncio.run(test_webhook())
    
    # Teraz odpala się główny bot

    asyncio.run(main_loop())
    async def test_webhook():
    test_item = {
        "title": "Test Item",
        "price_pln": 999,
        "url": "https://www.example.com",
        "image": "https://via.placeholder.com/150",
        "site": "TestSite",
        "size": "42"
    }
    await send_to_discord(test_item)
