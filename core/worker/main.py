from __future__ import annotations

import time


def main() -> None:
    while True:
        print("RetailOps worker heartbeat")
        time.sleep(30)


if __name__ == "__main__":
    main()
