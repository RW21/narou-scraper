import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--reset", action=argparse.BooleanOptionalAction, help="reset scrape history")
parser.add_argument("--start-from", type=str, help="The starting nid, inclusive")
parser.add_argument("--end-with", type=str, help="The ending nid, inclusive")
parser.add_argument('--log-file', type=str, help="Location of log file")
parser.add_argument('--skip-r18', type=str, help="Whether to skip R18 novels")
parser.set_defaults(log_file="scrape.log", reset=False, start_from="N9999ZZ", end_with="N0000AA", skip_r18=False)

script_args = parser.parse_args()
