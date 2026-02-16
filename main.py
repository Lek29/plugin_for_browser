import logging
import sys

import anyio
import pymorphy2
import aiohttp
import asyncio
import async_timeout
import time

from text_tools import split_by_words, calculate_jaundice_rate, load_charged_words
from adapters.inosmi_ru import sanitize
from adapters.exceptions import ArticleNotFound
from enum import Enum
from contextlib import contextmanager


TEST_ARTICLE = [
        'https://inosmi.ru/20260212/olimpiada-277075823.html',
        'https://inosmi.ru/20260213/kontslager-277106588.html',
        'https://inosmi.ru/20260213/merts-277104165.html',
        'https://inosmi.ru/not/exist.html',
        'https://lenta.ru/news/...',
        'https://lenta.ru/brief/2021/08/26/afg_terror/'
    ]

logger = logging.getLogger(__name__)


@contextmanager
def duration(url):
    start_time = time.monotonic()
    article_info = {"status": "UNKNOWN", "rate": None, "words": None}
    try:
        yield article_info
    finally:
        end_time = time.monotonic()
        logging.info(
            f"\nURL: {url}\n"
            f"Статус: {article_info['status']}\n"
            f"Рейтинг: {article_info['rate']}\n"
            f"Слов в статье: {article_info['words']}\n"
            f"Анализ закончен за {end_time - start_time:.2f} сек\n"
        )


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


async def processing_article(session, morph, url, charged_words, results):
    with duration(url) as info:
        status = ProcessingStatus.OK
        rate = None
        words_count = None

        try:
            async with async_timeout.timeout(3):
                async with session.get(url) as response:
                    response.raise_for_status()
                    html = await  response.text()
                    try:
                        clean_text = sanitize(html, plaintext=True)
                        words = split_by_words(morph, clean_text)
                        rate = calculate_jaundice_rate(words, charged_words)
                        words_count = len(words)
                    except ArticleNotFound:
                        status = ProcessingStatus.PARSING_ERROR

        except asyncio.TimeoutError:
            status = ProcessingStatus.TIMEOUT
        except (aiohttp.ClientError, aiohttp.http_exceptions.HttpProcessingError):
            status = ProcessingStatus.FETCH_ERROR

        info["status"] = status.value
        info["rate"] = rate
        info["words"] = words_count

        results.append({
            'url': url,
            'status': status.value,
            'score': rate,
            'words_count':words_count
        })


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def main():
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format='{levelname} - {name} - {message}',
        style='{'
    )

    morph = pymorphy2.MorphAnalyzer()
    charged_words = load_charged_words('charged_dict')

    results = []

    async with aiohttp.ClientSession() as session:
        async with anyio.create_task_group() as tg:
            for url in TEST_ARTICLE:
                tg.start_soon(processing_article, session, morph, url, charged_words, results)

    # for res in results:
    #     print(f"URL: {res['url']}\nСтатус: {res['status']}\nРейтинг: {res['score']}\nСлов: {res['words_count']}\n")

if __name__ == '__main__':
    asyncio.run(main())
