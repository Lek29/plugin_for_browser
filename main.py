import anyio
import pymorphy2
import aiohttp
import asyncio

from text_tools import split_by_words, calculate_jaundice_rate, load_charged_words
from adapters.inosmi_ru import sanitize

TEST_ARTICLE = [
        'https://inosmi.ru/20260212/olimpiada-277075823.html',
        'https://inosmi.ru/20260213/kontslager-277106588.html',
        'https://inosmi.ru/20260213/merts-277104165.html'
    ]

async def process_article(session, morph, url, charged_words):
    async with session.get(url) as response:
        response.raise_for_status
        html = await response.text()

    clean_text =sanitize(html, plaintext=True)
    words = split_by_words(morph, clean_text)
    rate = calculate_jaundice_rate(words, charged_words)

    print(f"URL: {url}")
    print(f"Рейтинг: {rate}")
    print(f"Слов в статье: {len(words)}\n")


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def main():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = load_charged_words('charged_dict')

    async with aiohttp.ClientSession() as session:
        async with anyio.create_task_group() as tg:
            for url in TEST_ARTICLE:
                tg.start_soon(
                    process_article, session,
                    morph, url, charged_words
                )

if __name__ == '__main__':
    asyncio.run(main())
