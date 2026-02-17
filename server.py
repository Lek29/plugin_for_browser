from aiohttp import web


async def handle_analyse(request):
    urls_raw = request.query.get('urls')
    if not urls_raw:
        return web.json_response(
            {"error": "bad request, no urls provided"},
            status=400
        )
    urls = urls_raw.split(',')

    return web.json_response({
        'urls': urls,
    })

if __name__ == '__main__':
    app = web.Application()

    app.add_routes([
        web.get('/', handle_analyse),
    ])

    web.run_app(app, port=8080)
