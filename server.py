import aiohttp
import anyio
from aiohttp import web
import asyncio
import pymorphy2
from functools import partial

from main import processing_article, ProcessingStatus
from text_tools import load_charged_words


async def handle_analyse(morph, charged_words, request):
    urls_raw = request.query.get('urls')
    if not urls_raw:
        return web.json_response(
            {"error": "bad request, no urls provided"},
            status=400
        )
    urls = urls_raw.split(',')

    max_urls_per_request = 10
    if len(urls) > max_urls_per_request:
        return web.json_response({'error': 'too many urls'}, status=400)

    results = []

    async with aiohttp.ClientSession() as session:
        async with anyio.create_task_group() as tg:
            for url in urls:
                tg.start_soon(
                    processing_article,
                    session,
                    morph,
                    url,
                    charged_words,
                    results
                )

    return web.json_response(results)


def make_app(morph_analyzer, words_dictonary):
    app_instance = web.Application()

    handler = partial(handle_analyse, morph_analyzer, words_dictonary)

    app_instance.add_routes([web.get('/analyse', handler)])

    return app_instance


if __name__ == '__main__':
    morph = pymorphy2.MorphAnalyzer()
    charged_words = load_charged_words('charged_dict')

    app = make_app(morph, charged_words)

    web.run_app(app, port=8080)
