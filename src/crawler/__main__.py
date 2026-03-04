import functools
from concurrent.futures import ThreadPoolExecutor, Executor, thread
from io import TextIOWrapper
import uuid
from uuid import uuid4
import os
import shutil
import aiohttp
from yarl import URL
import asyncio
from typing import cast, Callable, Awaitable, Coroutine, Any, reveal_type
import sys
import pathlib
from argparse import ArgumentParser, Namespace

thread_pool = ThreadPoolExecutor(max_workers=16)


def runs_in_executor[**P, R](
    executor: Executor,
) -> Callable[[Callable[P, R]], Callable[P, Coroutine[R, Any, Any]]]:
    def decorator(sync_func: Callable[P, R]) -> Callable[P, Coroutine[Any, Any, R]]:
        @functools.wraps(sync_func)
        async def runner(*args: P.args, **kwargs: P.kwargs) -> R:
            loop = asyncio.get_running_loop()
            binded = functools.partial(sync_func, *args, **kwargs)
            return await loop.run_in_executor(executor, binded)

        return runner

    return decorator


class CLIArguments(Namespace):
    input_file: pathlib.Path
    output_dir: pathlib.Path


def parse_args(argv: list[str]) -> CLIArguments:
    parser = ArgumentParser(prog="web-crawler")
    parser.add_argument(
        "-i",
        "--input-file",
        type=pathlib.Path,
        help="input file path",
        dest="input_file",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=pathlib.Path,
        help="output to save files",
        dest="output_dir",
    )
    args = CLIArguments()
    parser.parse_args(argv, namespace=args)
    return args

@runs_in_executor(thread_pool)
def save_to_file(path: pathlib.Path, data: bytes) -> None:
    with open(path, "wb") as output_file:
        output_file.write(data)


async def get_url_and_save(
    session: aiohttp.ClientSession,
    url: URL,
    output_dir: pathlib.Path,
) -> None:
    response = await session.get(url)
    response_content = await response.read()

    filename_parts = str(uuid.uuid4()) + ".".join(pathlib.Path(url.parts[-1]).suffixes)
    output_path = output_dir / filename_parts
    await save_to_file(output_path, response_content)


async def main() -> None:
    args = parse_args(sys.argv[1:])
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.input_file) as input_file:
        input_urls_raw = input_file.readlines()
        input_urls = [URL(url) for url in input_urls_raw]

    async with aiohttp.ClientSession() as session:
        tasks = [get_url_and_save(session, url, args.output_dir) for url in input_urls]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
