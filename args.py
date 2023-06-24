import argparse

parser = argparse.ArgumentParser(
    description="""
    This script will scrape narou novels.
    It will save the files in a sqlite database named novels.db.
    See models.py for the fields it can scrape.
    
    Example Usage:
    1. To scrape a range of novels, specify the starting and ending nids:
    python3 main.py --start-from N1955HZ --end-with N1955HZ 

    2. To scrape a specific novel, specify its nid:
    python3 main.py --nid n6879ig 

    3. To skip scraping R18 novels:
    python3 main.py --skip-r18 true 

    4. To specify the location of the log file:
    python3 main.py --log-file ./logs/scrape.log 
    
    このスクリプトはなろう小説をスクレイピングします。
    novels.dbという名前のsqliteデータベースに保存されます。
    取得できるフィールドは、models.pyを参照してください。
    
    使用例:
    1. 小説の範囲を指定し、スクレイピングするには、開始と終了のnidを設定します:
    python3 main.py --start-from N1955HZ --end-with N1955HZ 

    2. 特定の小説をスクレイピングするには、そのnidを指定します:
    python3 main.py --nid n6879ig 

    3. R18の小説のスクレイピングをスキップするには:
    python3 main.py --skip-r18 true 

    4. ログファイルの場所を指定するには:
    python3 main.py --log-file ./logs/scrape.log 
    
    """,
    epilog="""
    """,
    formatter_class=argparse.RawTextHelpFormatter
)

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
