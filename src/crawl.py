import argparse, aiohttp, asyncio


def parser():
    prs = argparse.ArgumentParser()
    prs.add_argument('url', nargs='+')
    arg = prs.parse_args()
    return arg.url


async def main():
    urls = parser()
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:8888/api/v1/tasks/', json={"urls": urls}) as response:
            resp = await response.json()
        while resp.get('status') == "Running":
            async with session.get(f'http://127.0.0.1:8888/api/v1/tasks/{resp["id"]}') as response:
                resp = await response.json()
            await asyncio.sleep(1)
        for result in resp['result']:
            print(result['code'], '\t', result['url'])


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except BaseException as e:
        print(e)
