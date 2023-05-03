from pydantic import BaseModel
from fastapi import FastAPI
from uuid import uuid4
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
    tasks[task_id].status = "Ready"
    logging.info(f"Task {task_id} is ready")


async def try_connection(session, url_dict):
    try:
        async with session.get(url=url_dict['url']) as response:
            url_dict["code"] = response.status
    except BaseException as _ex:
        logging.info(f"Connection fail: {_ex}")
        url_dict["code"] = 400


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
    await asyncio.sleep(10)
    if tasks.get(task_id):
        tasks.pop(task_id)
        logging.info(f"Task {task_id} have been removed")
