import argparse

from src.services.parser.parser_registry import PARSER_REGISTRY


def list_parsers():
    print("Available parsers:")
    for name, meta in PARSER_REGISTRY.items():
        status = "available" if meta.available else f"unavailable ({meta.reason})"
        print(f"- {name}: {status}")



def main():
    parser = argparse.ArgumentParser(description="Parser CLI")
    parser.add_argument("--list", action="store_true", help="List all available parsers")
    args = parser.parse_args()

    if args.list:
        list_parsers()


if __name__ == "__main__":
    main()
