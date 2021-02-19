# Actyon

`actyon` can be used natively or via the provided interface extensions [Flux](flux/) and [State Machine](sm/).

## Simple Usage

Define an interface class for your actyon, like `MyResult`.

Create a producer with return annotation `MyResult` or `List[MyResult]`:

```python
from actyon import produce

@produce("my_actyon")
async def my_producer(dependency: MyDependency) -> MyResult:
    # your magic code ...
    return my_result
```

Create a consumer taking exactly one parameter of type `List[MyResult]`:

```python
from actyon import consume

@consume("my_actyon")
async def my_consumer(results: List[MyResult]) -> None:
    # do whatever you want with your results
```

Finally, execute your actyon:

```python
from actyon import execute

await execute("my_actyon", dependencies)
```

By the way, `dependencies` can be any kind of object (iterable or simply an instance of your favorite class). By handing it over to the `execute` method, it will be crawled and necessary objects will be extracted and handed over to all producers accordingly.

## Working with `Actyon`

Create an `Actyon`:

```python
from actyon import Actyon

my_actyon: Actyon = Actyon[MyResult]("my_actyon")
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

Execute:

```python
await my_actyon.execute(dependencies)
```

## Example: Github API

Please find the code [here](https://github.com/neatc0der/actyon/tree/master/examples/github_api.py).
