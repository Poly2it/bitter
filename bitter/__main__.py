from pathlib import Path

import argparse

from .terminal import error_collector

from .compiler import compile_code

import cProfile

import pstats

def main():
    parser = argparse.ArgumentParser(description="Bitter")

    parser.add_argument(
        "action", 
        choices=["compile", "new"], 
        help="Action to perform"
    )
    parser.add_argument(
        "path", 
        nargs="?", 
        help="Path to the Goboscript code file"
    )
    parser.add_argument(
        "-d", "--debug", 
        action="store_true", 
        help="Enable debug mode. This will write function timing data to 'profile.prof' (raw) and 'profile.txt' (readable). It will also dump the json to 'PROJECT_NAME.debug.json'.' "
    )

    args = parser.parse_args()

    if args.action == "compile":
        if not args.path:
            parser.error("Path argument is required for 'compile' action")

        if args.debug:
            pr = cProfile.Profile()
            pr.enable()
            compile_code(Path(args.path), args.debug)
            pr.disable()
            output_file = 'profile.prof'
            pr.dump_stats(output_file)

            with open('profile.txt', 'w') as f:
                p = pstats.Stats(output_file, stream=f)
                p.sort_stats('cumulative')
                p.print_stats()
        else:
            compile_code(Path(args.path), args.debug)
        
    elif args.action == "new":
        # TODO: Implement new
        pass
    else:
        parser.error("Invalid action")

    error_collector.render()

    if len(error_collector.errors) > 0:
        exit(1)
    else:
        exit(0)

if __name__ == '__main__':
    main()