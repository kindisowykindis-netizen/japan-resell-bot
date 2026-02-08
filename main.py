import aiohttp
import asyncio
from bs4 import BeautifulSoup
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
    items = []

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")

            for product in soup.select("li"):
                try:
                    title_tag = product.select_one("h3")
                    if not title_tag:
                        continue
                    title = title_tag.text.strip()

                    link_tag = product.select_one("a")
                    if not link_tag:
                        continue
                    link = "https://www.mercari.com" + link_tag.get("href")

                    price_tag = product.select_one(".items-box-price__current-price")
                    if not price_tag:
                        continue
                    price_jpy = int(price_tag.text.replace("¥", "").replace(",", ""))
                    price_pln = jpy_to_pln(price_jpy)

                    if price_pln > MAX_PRICE_PLN:
                        continue

                    img_tag = product.select_one("img")
                    img = img_tag["src"] if img_tag else None

                 size = "brak / nieznany"

                    items.append({
                        "title": title[:250],
                        "price_pln": price_pln,
                        "url": link,
                        "image": img,
                        "site": "Mercari JP",
                        "size": size
                    })

                except:
                    continue

    return items

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

async def main_loop():
    while True:
        print("🔍 Sprawdzam wszystkie frazy...")
        for keyword in KEYWORDS:
            items = await search_mercari(keyword)
            print(f"🔹 {keyword}: {len(items)} wyników")
            for item in items:
                print(f"✅ Wysyłam: {item['title']}")
                await send_to_discord(item)
                await asyncio.sleep(1)

        print(f"⏳ Czekam {CHECK_INTERVAL}s")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(test_webhook())
    asyncio.run(main_loop())
