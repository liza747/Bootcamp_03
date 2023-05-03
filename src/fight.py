from enum import Enum, auto
from random import choice
import asyncio, time


class Action(Enum):
    HIGHKICK = auto()
    LOWKICK = auto()
    HIGHBLOCK = auto()
    LOWBLOCK = auto()


contr_action = {Action.HIGHKICK: Action.HIGHBLOCK,
                Action.LOWKICK: Action.LOWBLOCK,
                Action.HIGHBLOCK: Action.LOWKICK,
                Action.LOWBLOCK: Action.HIGHKICK}
hit_actions = [Action.HIGHKICK, Action.LOWKICK]


class Agent:

    def __aiter__(self, health=5):
        self.health = health
        self.actions = list(Action)
        return self

    async def __anext__(self):
        return choice(self.actions)


async def fight(num: str = ""):
    agent = aiter(Agent())
    async for action in agent:
        neo_act = contr_action[action]
        if neo_act in hit_actions:
            agent.health -= 1
        print(f"Agent: {action}, Neo: {neo_act}, Agent {num} Health: {agent.health}")
        await asyncio.sleep(0.001)
        if agent.health < 1:
            break


async def fightmany(n):
    task = []
    for ag in range(n):
        task.append(asyncio.create_task(fight(str(ag + 1))))

    await asyncio.gather(*task)


async def main(n):
    if n != 0:
        await fightmany(n)
    else:
        await fight()
    print("Neo wins!")


if __name__ == "__main__":
    asyncio.run(main(0))
