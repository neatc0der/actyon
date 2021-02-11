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

## Simple Usage

Define an interface class for your actyon, like `MyResult`.

Create a producer with return annotation `MyResult` or `List[MyResult]`:

```python
from actyon import produce

@produce("my_thing")
async def my_producer(dependency: MyDependency) -> MyResult:
    # your magic code ...
    return my_result
```

Create a consumer taking exactly one parameter of type `List[MyResult]`:

```python
from actyon import consume

@consume("my_thing")
async def my_consumer(results: List[MyResult]) -> None:
    # do whatever you want with your results
```

Finally, execute your actyon:

```python
from actyon import execute

execute("my_thing", dependencies)
```

By the way, `dependencies` can be any kind of object (iterable or simply an instance of your favorite class). By handing it over to the `execute` method, it will be crawled and necessary objects will be extracted and handed over to all producers accordingly.

## Usage of class `Actyon`

Create an `Actyon`:

```python
from actyon import Actyon

my_actyon: Actyon = Actyon[MyResult]("my_thing")
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

# or use the generalized decorator
@consume("my_thing")
async def my_consumer(results: List[MyResult]) -> None:
    # do whatever you want with your results
```

Execute:

```python
my_actyon.execute(dependencies)
```

## Examples

* [Github API](https://github.com/neatc0der/actyon/tree/master/examples/github_api.py)

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
