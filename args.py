import argparse

parser = argparse.ArgumentParser(description="Scrape narou novels")
parser.add_argument("--reset", action="store_true", default=False,
                    help="Reset scrape history (default: %(default)s)")
parser.add_argument("--start-from", type=str, default="N9999ZZ",
                    help="The starting nid, inclusive (default: %(default)s)")
parser.add_argument("--end-with", type=str, default="N0000AA",
                    help="The ending nid, inclusive (default: %(default)s)")
parser.add_argument('--log-file', type=str, default="scrape.log",
                    help="Location of log file (default: %(default)s)")
parser.add_argument('--skip-r18', type=argparse.BooleanOptionalAction, default=False,
                    help="Whether to skip R18 novels (default: %(default)s)")
parser.add_argument('--nid', type=str,
                    help="The nid to scrape, if this is set, --start-from and --end-with are ignored")
parser.add_argument("--skip-content", action="store_true", default=False,
                    help="When this is enabled, it will skip scraping novel content (default: %(default)s)")
parser.add_argument("--skip-impression", action="store_true", default=False,
                    help="When this is enabled, it will skip scraping novel impression(default: %(default)s)")

parser.set_defaults(log_file="scrape.log", reset=False, start_from="N9999ZZ", end_with="N0000AA", skip_r18=False)

script_args = parser.parse_args()
