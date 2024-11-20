import argparse
import configparser
import os

from .commands import add, remove, list_paths, edit_config, rename

def main():
    parser = argparse.ArgumentParser(description="Command-line interface for managing paths in a config file.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    parser_init = subparsers.add_parser("init", help="Initialize local path store")
    parser_add = subparsers.add_parser("add", help="Add a path")
    parser_add.add_argument("name", help="Name of the path")
    parser_add.add_argument("path", help="Path to be added")
    parser_add.add_argument("--parent", nargs="?", help="Path to be added")
    parser_remove = subparsers.add_parser("remove", help="Remove a path")
    parser_remove.add_argument("name", help="Name of the path to be removed")
    parser_list = subparsers.add_parser("list", help="List stored paths")
    parser_edit = subparsers.add_parser("edit", help="Edit config file directly")
    parser_rename = subparsers.add_parser("rename", help="Rename a path")
    parser_rename.add_argument("old_name", help="Old name of the path")
    parser_rename.add_argument("new_name", help="New name of the path")

    args = parser.parse_args()

    if args.command == "init":
        initialize()
    elif args.command == "add":
        add(args.name, args.path, parent=args.parent)
    elif args.command == "remove":
        remove(args.name)
    elif args.command == "list":
        list_paths()
    elif args.command == "edit":
        edit_config()
    elif args.command == "rename":
        rename(args.old_name, args.new_name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
