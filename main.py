
import argparse

from src.vector_store import (
    build_index,
    search_index,
)


def main():
    parser = argparse.ArgumentParser(
        description="Tamil Nadu Agriculture PDF Search"
    )

    parser.add_argument(
        "command",
        choices=["index", "search"],
    )

    parser.add_argument(
        "--query",
        default="",
    )

    args = parser.parse_args()

    if args.command == "index":
        build_index()

    elif args.command == "search":
        if not args.query.strip():
            parser.error(
                "--query is required for search"
            )

        search_index(args.query)


if __name__ == "__main__":
    main()
