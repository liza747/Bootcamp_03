from redis.asyncio import from_url
from urllib.parse import urlparse
from pydantic import BaseModel
from fastapi import FastAPI
from uuid import uuid4
from json import loads
import asyncio
import aiohttp
import logging


class UrlList(BaseModel):
    urls: list[str]


class Task(BaseModel):
    status: str
    id: str
    result: list[dict]


tasks: dict = {}
cache_clear_timeout = 15
redis = from_url(url="redis://127.0.0.1", port=6379)
redis.set("domains_counter", str({}))
logging.basicConfig(level=logging.INFO, format='\033[32m%(levelname)s\033[0m:\t  %(message)s')
app = FastAPI()


@app.post("/api/v1/tasks/", status_code=201)
async def run_task(data: UrlList):
    task_id = str(uuid4().hex)
    tasks[task_id] = Task(status="Running", id=task_id,
                          result=[{"url": url} for url in  data.urls])
    task = asyncio.create_task(url_check(task_id))
    asyncio.gather(task)
    return tasks[task_id]


async def url_check(task_id):
    logging.info(f"Task {task_id} run")
    async with aiohttp.ClientSession() as session:
        url_list: list = tasks[task_id].result
        for i in range(len(url_list)):
            await asyncio.sleep(0.1)
            await try_connection(session, url_list[i])
            await add_domain_amount(url_list[i]['url'])
    tasks[task_id].status = "Ready"
    logging.info(f"Task {task_id} is ready")


async def add_domain_amount(url):
    domain = urlparse(url).netloc
    domains_counter = await get_domains_counter_dict()
    if domains_counter.get(domain):
        domains_counter[domain] += 1
    else:
        domains_counter[domain] = 1
    logging.info(f"Current domains {domain} amount: {domains_counter[domain]}")
    await redis.set("domains_counter", str(domains_counter))


async def get_domains_counter_dict() -> dict:
    domains_bin = await redis.get("domains_counter")
    if domains_bin is None:
        await redis.set("domains_counter", str({}))
        domains_bin = await redis.get("domains_counter")
    domains_str = domains_bin.decode("utf-8").replace("'", "\"")
    domains_counter = loads(domains_str)
    return domains_counter


async def try_connection(session, url_dict):
    code = await redis.get(url_dict['url'])
    if code:
        url_dict["code"] = code
        logging.info("Got cached code")
        return
    try:
        async with session.get(url=url_dict['url']) as response:
            url_dict["code"] = response.status
    except BaseException as _ex:
        logging.info(f"Connection fail: {_ex}")
        url_dict["code"] = 400
    await redis.set(url_dict['url'], url_dict["code"])


@app.get("/api/v1/tasks/{id}")
async def get_task(id):
    if tasks.get(id):
        if tasks[id].status == "Ready":
            task = asyncio.create_task(remove_task(id))
            asyncio.gather(task)
        return tasks[id]
    else:
        return f"There is no task with id {id} or was removed"


async def remove_task(task_id):
    await asyncio.sleep(cache_clear_timeout)
    if tasks.get(task_id):
        domains_counter = await get_domains_counter_dict()
        for url in tasks[task_id].result:
            domain = urlparse(url['url']).netloc
            await redis.delete(url['url'])
            domains_counter.pop(domain)
            await redis.set("domains_counter", str(domains_counter))
        tasks.pop(task_id)
        logging.info(f"Cache of task {task_id} have been removed")
