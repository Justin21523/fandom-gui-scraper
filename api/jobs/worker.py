import logging
import os

from rq import Worker

from api.jobs.queue import get_queue, get_redis_raw


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    queue = get_queue()
    worker = Worker([queue], connection=get_redis_raw())
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
