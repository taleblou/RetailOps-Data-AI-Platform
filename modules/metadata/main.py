from __future__ import annotations

import time

SERVICE_NAME = "metadata"


def main() -> None:
    while True:
        print(f"RetailOps {SERVICE_NAME} service heartbeat")
        time.sleep(30)


if __name__ == "__main__":
    main()
