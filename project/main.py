from multiprocessing import Process

from Escort.escort_bot import main as escort_main
from Escort.support_bot import main as support_main
from app.app import build_application


def run_main_bot() -> None:
    build_application()


def run_escort_bot() -> None:
    escort_main()


def run_support_bot() -> None:
    support_main()


if __name__ == "__main__":
    processes = [
        Process(target=run_main_bot),
        Process(target=run_escort_bot),
        Process(target=run_support_bot),
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join()
