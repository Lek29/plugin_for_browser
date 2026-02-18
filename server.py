import json
import os
from functools import partial

import redis.asyncio as redis
import aiohttp
import anyio
import pymorphy2
from aiohttp import web

from main import processing_article
from text_tools import load_charged_words


async def handle_analyse(morph, charged_words, redis_conn, request):
    urls_raw = request.query.get('urls')
    if not urls_raw:
        return web.json_response(
            {'error': 'bad request, no urls provided'},
            status=400
        )
    urls = list(set(urls_raw.split(',')))

    max_urls_per_request = 10
    if len(urls) > max_urls_per_request:
        return web.json_response({'error': 'too many urls'}, status=400)

    results = []
    urls_to_analyze = []

    for url in urls:
        cached_data = await redis_conn.get(url)

        if cached_data:
            results.append(json.loads(cached_data))
        else:
            urls_to_analyze.append(url)

    if urls_to_analyze:
        new_results = []

        async with aiohttp.ClientSession() as session:
            async with anyio.create_task_group() as tg:
                for url in urls:
                    tg.start_soon(
                        processing_article,
                        session,
                        morph,
                        url,
                        charged_words,
                        new_results
                    )

        for res in new_results:
            await redis_conn.set(res['url'], json.dumps(res), ex=180)

            results.append(res)

    return web.json_response(results)


def make_app(morph_analyzer, words_dictionary):
    app_instance = web.Application()
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_password = os.getenv('REDIS_PASSWORD', None)
    redis_conn = redis.Redis(
        host=redis_host,
        port=6379,
        decode_responses=True,
        password=redis_password
    )

    handler = partial(handle_analyse, morph_analyzer, words_dictionary, redis_conn)

    app_instance.add_routes([web.get('/analyse', handler)])

    return app_instance


if __name__ == '__main__':
    morph = pymorphy2.MorphAnalyzer()
    charged_words = load_charged_words('charged_dict')

    app = make_app(morph, charged_words)

    web.run_app(app, port=8080)
