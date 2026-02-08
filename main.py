import aiohttp
import asyncio
from bs4 import BeautifulSoup
from config import *

HEADERS = {"User-Agent": "Mozilla/5.0"}

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
            {"name": "📍 Źródło", "value": item["site"], "inline": True},
        ],
        "image": {"url": item["image"]},
        "footer": {"text": "Japan Marketplace Monitor"}
    }
    async with aiohttp.ClientSession() as session:
        await session.post(WEBHOOK_URL, json={"embeds": [embed]})

# --- Scraping Mercari ---
async def search_mercari(keyword):
    url = f"https://www.mercari.com/jp/search/?keyword={keyword}"
    results = []
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as r:
            html = await r.text()
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
                    link = "https://www.mercari.com" + link_tag["href"]
                    if link in sent_links:
                        continue
                    price_tag = product.select_one(".items-box-price__current-price")
                    if not price_tag:
                        continue
                    price_jpy = int(price_tag.text.replace("¥", "").replace(",", ""))
                    price_pln = jpy_to_pln(price_jpy)
                    if price_pln > MAX_PRICE_PLN:
                        continue
                    img_tag = product.select_one("img")
                    img = img_tag["src"] if img_tag else None
                    results.append({
                        "title": title[:250],
                        "price_pln": price_pln,
                        "url": link,
                        "image": img,
                        "site": "Mercari JP"
                    })
                except:
                    continue
    return results

# --- Scraping Yahoo! Auctions Japan ---
async def search_yahoo(keyword):
    url = f"https://auctions.yahoo.co.jp/search/search?p={keyword}"
    results = []
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as r:
            html = await r.text()
            soup = BeautifulSoup(html, "html.parser")
            for product in soup.select(".Product"):
                try:
                    title_tag = product.select_one(".Product__title")
                    if not title_tag:
                        continue
                    title = title_tag.text.strip()
                    link_tag = product.select_one("a")
                    if not link_tag:
                        continue
                    link = link_tag["href"]
                    if link in sent_links:
                        continue
                    price_tag = product.select_one(".Price__value")
                    if not price_tag:
                        continue
                    price_jpy = int(price_tag.text.replace("¥", "").replace(",", ""))
                    price_pln = jpy_to_pln(price_jpy)
                    if price_pln > MAX_PRICE_PLN:
                        continue
                    img_tag = product.select_one("img")
                    img = img_tag["src"] if img_tag else None
                    results.append({
                        "title": title[:250],
                        "price_pln": price_pln,
                        "url": link,
                        "image": img,
                        "site": "Yahoo! Auctions JP"
                    })
                except:
                    continue
    return results

# --- Scraping Rakuten ---
async def search_rakuten(keyword):
    url = f"https://search.rakuten.co.jp/search/mall/{keyword}/"
    results = []
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as r:
            html = await r.text()
            soup = BeautifulSoup(html, "html.parser")
            for product in soup.select(".searchresultitem"):
                try:
                    title_tag = product.select_one(".title")
                    if not title_tag:
                        continue
                    title = title_tag.text.strip()
                    link_tag = product.select_one("a")
                    if not link_tag:
                        continue
                    link = link_tag["href"]
                    if link in sent_links:
                        continue
                    price_tag = product.select_one(".important")
                    if not price_tag:
                        continue
                    price_jpy = int(price_tag.text.replace("￥", "").replace(",", "").replace("¥", ""))
                    price_pln = jpy_to_pln(price_jpy)
                    if price_pln > MAX_PRICE_PLN:
                        continue
                    img_tag = product.select_one("img")
                    img = img_tag["src"] if img_tag else None
                    results.append({
                        "title": title[:250],
                        "price_pln": price_pln,
                        "url": link,
                        "image": img,
                        "site": "Rakuten JP"
                    })
                except:
                    continue
    return results

async def main_loop():
    while True:
        print("🔍 Szukam ofert...")
        # wszystkie serwisy równolegle
        tasks = []
        for kw in KEYWORDS:
            tasks.append(search_mercari(kw))
            tasks.append(search_yahoo(kw))
            tasks.append(search_rakuten(kw))
        all_results = await asyncio.gather(*tasks)

        # płaskie listowanie i wysyłka
        for result_list in all_results:
            for item in result_list:
                if item["url"] not in sent_links:
                    sent_links.add(item["url"])
                    print(f"➡️ wysyłam: {item['title']}")
                    await send_to_discord(item)
                    await asyncio.sleep(1)

        print(f"⏳ Czekam {CHECK_INTERVAL}s...")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main_loop())
