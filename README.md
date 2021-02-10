# actyon

> Action with a Y! Why? Cause `async` is in the box.

[![MIT license](https://badgen.net/github/license/neatc0der/actyon)](https://github.com/neatc0der/actyon/blob/master/LICENSE)
[![PyPI](https://badgen.net/pypi/v/actyon)](https://pypi.org/project/actyon/)
[![Latest Release](https://badgen.net/github/release/neatc0der/actyon/latest)](https://github.com/neatc0der/actyon/releases/latest)
[![Open Issues](https://badgen.net/github/open-issues/neatc0der/actyon)](https://github.com/neatc0der/actyon/issues)
[![Open PRs](https://badgen.net/github/open-prs/neatc0der/actyon)](https://github.com/neatc0der/actyon/pulls)

`actyon` offers an approach on a multiplexed flux pattern using coroutines ([PEP 492](https://www.python.org/dev/peps/pep-0492/)).

## Idea

* An actyon is defining an isolated execution run.
* Producers are called on _all combinations_ of input dependencies.
* Consumers are called on _all results at once_.
* Dependencies are available in any kind of structure.
* Dependencies are injected according to function signatures.
* Missing dependencies are ignored, unless no producer can be executed.

## Implications

* Synchronization points are
  * Start
  * Conclusion of all producers
  * End
* Producers are called asynchronously at once
* Consumers are called asynchronously at once
* **Typing is mandatory**
* **Coroutines for producers and consumers are mandatory**
* **Python 3.8+ is required**

## Install

```bash
pip install actyon
```

## Usage

Create an `Actyon`:

```python
from actyon import Actyon
my_actyon: Actyon = Actyon[MyResult]("unique_name")
```

Create a producer:

```python
@my_actyon.producer
async def my_producer(dependency: MyDependency) -> MyResult:
    # your magic code ...
    return my_result
```

Create a consumer:

```python
@my_actyon.consumer
async def my_consumer(results: List[MyResult]) -> None:
    # do whatever you want with your results
```

Finally, execute your actyon:

```python
from actyon import execute
execute("unique_name", dependencies)

# or call an actyon directly:
my_actyon.execute(dependencies)
```

By the way, `dependencies` can be any kind of object (iterable of instance of an arbitrary class). By handing it over to the `execute` method, it will be crawled and necessary objects will be extracted and handed over to all producers accordingly.

## Example

```python
from datetime import datetime
import os
import re
from typing import Any, Dict, List

import attr
from actyon import Actyon
from aiohttp import ClientSession
from asyncio import run
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


def camal_to_snake(camal_case: str) -> str:
    return re.sub("(?!^)([A-Z]+)", r"_\1", camal_case).lower()


@attr.s(slots=True)
class Rate:
    limit: int = attr.ib()
    cost: int = attr.ib()
    remaining: int = attr.ib()
    reset_at: datetime = attr.ib(converter=parse)


rate_actyon: Actyon = Actyon[Rate]("rate")


@rate_actyon.producer
async def rate_producer(github: GitHubAPI) -> List[Rate]:
    response: Dict[str, Any] = await github.graphql(query)
    return [
        Rate(
            **{
                camal_to_snake(key): value
                for key, value in response["rateLimit"].items()
            },
        ),
    ]


@rate_actyon.consumer
async def rate_consumer(rates: List[Rate]) -> None:
    for rate in rates:
        print(rate)
    
    if len(rates) == 0:
        print("no rates found")


async def main():
    async with ClientSession() as session:
        await rate_actyon.execute(
            GitHubAPI(
                session=session,
                requester=os.environ["GITHUB_USER"],
                oauth_token=os.environ["GITHUB_TOKEN"],
            )
        )


if __name__ == "__main__":
    run(main())
```

## Nerd Section

### Great, but who needs this?

First of all, this is an open source project for everybody to use, distribute, adjust or simply carve out whatever you need. For me it's a case study on dependency injection and coroutines, so don't expect this to be a masterpiece.

### Are you serious? Python is not Java, we don't need DI.

Aside from answer N° 1, I want to make clear I'm not a java developer getting started with python. I love python and its capabilities. So making python even greater and more accessible to the people is the key to me. Maybe DI is a step towards that, maybe it's not. Still, this code may provide other developers with an idea to accomplish exactly that.

### Gotcha. Why did you decide on this approach?

Once you start developing software, you want it to simplify things. That's the whole definition of a software developer by the way: we are lazy by definition. Anyway, this code shows how you can multiplex tasks and sync them on the interface level. Your tasks are executed asynchronously all together, results are gathered and in the end they are being processed further - again, asynchronously all together. The decorator functionality allows for the application of the SOLID principle, which is pretty need:

* Single-responsibility principle
* Open–closed principle
* Liskov substitution principle
* Interface segregation principle
* Dependency inversion principle

In this code the bottom two are quite shallow and not really applicable, but let's not get stuck with this. Another key feature of the functional interface is the simplicity. Define an action, use the decorators on whatever functions you have and just execute it. It even got a nice console output when you add `hook=actyon.DisplayHook()` to the `Actyon`'s constructor. Try it out, but caution: parallel actyon execution will break the rendering.
