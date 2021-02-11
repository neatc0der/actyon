import os
import re
from asyncio import run
from datetime import datetime
from typing import Any, Dict, List

from actyon import consume, execute, produce
from aiohttp import ClientSession
import attr
from dateutil.parser import parse
from gidgethub.aiohttp import GitHubAPI


query: str = """
{
  viewer {
    login
  }
  rateLimit {
    limit
    cost
    remaining
    resetAt
  }
}
"""


def camel_to_snake(camel_case: str) -> str:
    return re.sub("(?!^)([A-Z]+)", r"_\1", camel_case).lower()


@attr.s(slots=True)
class Rate:
    limit: int = attr.ib()
    cost: int = attr.ib()
    remaining: int = attr.ib()
    reset_at: datetime = attr.ib(converter=parse)


@produce("rate")
async def rate_producer(github: GitHubAPI) -> Rate:
    response: Dict[str, Any] = await github.graphql(query)
    return Rate(
        **{
            camel_to_snake(key): value
            for key, value in response["rateLimit"].items()
        },
    ),


@consume("rate")
async def rate_consumer(rates: List[Rate]) -> None:
    for rate in rates:
        print(rate)

    if len(rates) == 0:
        print("no rates found")


async def main():
    async with ClientSession() as session:
        await execute(
            "rate",
            dependency=GitHubAPI(
                session=session,
                requester=os.environ["GITHUB_USER"],
                oauth_token=os.environ["GITHUB_TOKEN"],
            )
        )


if __name__ == "__main__":
    run(main())
