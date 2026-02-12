import pymorphy2
import aiohttp
import asyncio

from text_tools import split_by_words, calculate_jaundice_rate
from adapters.inosmi_ru import sanitize


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def main():
    url = 'https://inosmi.ru/20260212/olimpiada-277075823.html'
    test_charged_words = ['политический', 'украина', 'лозунги']

    morph = pymorphy2.MorphAnalyzer()

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            html = await response.text()

    clean_text = sanitize(html, plaintext=True)

    article_words = split_by_words(morph, clean_text)
    rate = calculate_jaundice_rate(article_words, test_charged_words)

    print(f'Рейтинг: {rate}')
    print(f'Слов в статье: {len(article_words)}')

if __name__ == '__main__':
    asyncio.run(main())
