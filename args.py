import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--reset", action=argparse.BooleanOptionalAction, help="reset scrape history")
parser.add_argument("--start_from", type=str, help="The starting nid, inclusive")
parser.add_argument("--end_with", type=str, help="The ending nid, inclusive")
parser.add_argument('--log_file', type=str, help="Location of log file")
parser.set_defaults(log_file="scrape.log", reset=False, start_from="N9999ZZ", end_with="N0000AA")

script_args = parser.parse_args()
