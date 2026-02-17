import aiohttp
import pytest

from main import ProcessingStatus, processing_article


@pytest.mark.asyncio
async def test_processing_article_fetch_error():
    results = []

    url = 'https://this-site-does-not-exist-123.com'

    async with aiohttp.ClientSession() as session:
        await processing_article(session, None, url, {}, results)

    assert results[0]['status'] == ProcessingStatus.FETCH_ERROR
    assert results[0]['url'] == url


@pytest.mark.asyncio
async def test_processing_article_parsing_error():
    results = []
    url = 'https://google.com'

    async with aiohttp.ClientSession() as session:
        await processing_article(session, None, url, {}, results)

    assert results[0]['status'] == ProcessingStatus.PARSING_ERROR


@pytest.mark.asyncio
async def test_processing_article_timeout():
    results = []

    url = 'https://httpbin.org/delay/5'

    async with aiohttp.ClientSession() as session:
        await processing_article(session, None, url, {}, results)

    assert results[0]['status'] == ProcessingStatus.TIMEOUT
