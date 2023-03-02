from datetime import date
import time
import zipfile
import subprocess
import argparse
import os

import sentinelsat

from typing import Generator, Any, Final

########################

# Query scihub API for Sentinel2 product

# Simple CLI to query, download and correct sentinel2 tiles

########################


# connect to the API
# A .netrc file with username and password must be present in the home folder
api = sentinelsat.SentinelAPI(None, None, "https://scihub.copernicus.eu/dhus")
import pdb


def _query_by_tile_names(
    tiles, level="2A", date_range=("20150101", "20170101"), cc=(0, 5)
) -> None:
    for tl in tiles:
        # pdb.set_trace()
        products = api.query(
            platformname="Sentinel-2",
            processingLevel=f"Level-{level}",
            date=date_range,
            filename=f"*{tl}*",
            cloudcoverpercentage=cc,
        )
        print(f"Tile: {tl}")
        print("\n")

        for k in products.keys():
            begin_acquisition_date = products.get(k)["beginposition"].date()
            date = begin_acquisition_date.strftime("%m/%d/%Y")
            size = products.get(k)["size"]
            uuid = products.get(k)["uuid"]
            print(f"{date}, {size}, {uuid}\n")


def _download_by_uuid(tiles, outdir, keep_zip=True) -> None:
    for name, uuid in tiles:
        time.sleep(5)
        print(f"Trying tile name: {name}, uuid: {uuid}")
        try:
            products = api.download(uuid, outdir)
            print(f"{name} downloaded")
        except sentinelsat.exceptions.LTATriggered:
            print(f"{uuid} not online, skipped..")
            continue
        except sentinelsat.exceptions.ServerError:
            print(f"Got server error..")
            return
        try:
            print(f"Try to unzip...")
            fzip = ".".join([products["title"], "zip"])
            fzippath = os.path.join(outdir, fzip)
            with zipfile.ZipFile(fzippath, "r") as zip_ref:
                zip_ref.extractall(outdir)
        except zipfile.BadZipFile:
            print(f"something went wrong with unzipping ..")
            os.remove(fzippath)
            continue

        if not keep_zip:
            os.remove(fzippath)


def _correct_1c_to_2a(indir):
    # this works only when run on the dcorr server
    my_env = os.environ.copy()
    my_env["PATH"] = "/home/ubuntu/Sen2Cor-02.08.00-Linux64/bin:" + my_env["PATH"]
    my_env["SEN2COR_HOME"] = "/home/ubuntu/sen2cor/2.8"
    my_env[
        "SEN2COR_BIN"
    ] = "/home/ubuntu/Sen2Cor-02.08.00-Linux64/lib/python2.7/site-packages/sen2cor"
    my_env["LC_NUMERIC"] = "C"
    my_env["GDAL_DATA"] = "/home/ubuntu/Sen2Cor-02.08.00-Linux64/share/gdal"
    my_env["GDAL_DRIVER_PATH"] = "disable"

    # load all tiles fo correction
    fpaths = []
    for f in fpaths:
        print(f"Start correction for tile {f}")
        # get the full path to tile
        # fpath = os.path.join(full_basedir, tile_db.fname)

        cmd = (f"L2A_Process {f}",)

        try:
            result = subprocess.check_output(cmd, env=my_env, shell=True)
        except subprocess.CalledProcessError as e:
            print(e.output)
            continue

        print(f"Finished correction for tile {f}")

        # new_fname = [_dir for _dir in os.listdir(full_basedir) if
        #    fnmatch.fnmatch(_dir, f'*_MSIL2A_*_{tile_db.name}_*')][0]


def cli() -> Any:
    parser: Any = argparse.ArgumentParser(
        description="Search, download and correct sentinel2 products"
    )
    subparsers: Any = parser.add_subparsers(help="Commands", dest="command")

    # create the parser for the "query" command
    parser_query: Any = subparsers.add_parser("query", help="query the scihub database")
    parser_query.add_argument(
        "-n", "--names", type=str, help="Space separated names of the tiles"
    )
    parser_query.add_argument(
        "-d",
        "--date",
        type=str,
        help="Space separated date range in this format, yyyyMMdd yyyyMMdd",
    )
    parser_query.add_argument(
        "-l", "--level", type=str, help="processing level, 2A or 1C"
    )

    # create the parser for the "download" command
    parser_download: Any = subparsers.add_parser(
        "download", help="download and unzip sentinel2 products from scihub"
    )
    parser_download.add_argument("-n", "--name", type=str, help="name of the tile")
    parser_download.add_argument(
        "-id",
        "--uuid",
        type=str,
        help="uuid of the tile",
    )
    parser_download.add_argument(
        "-d", "--outdir", type=str, help="directory path to download the tile"
    )

    # create the parser for the "correct" command
    parser_correct: Any = subparsers.add_parser(
        "correct", help="atmospheric correction of sentinel2 tiles via sen2corr"
    )
    parser_correct.add_argument(
        "-d", "--indir", type=str, help="directory path containing the tiles to correct"
    )
    return parser


def main() -> None:
    parser = cli()
    args = parser.parse_args()

    print(f"args: {args}")

    if args.command == "query":
        tiles_name = args.names.split()
        tiles_date = tuple(args.date.split())
        tiles_level = args.level.split()
        _query_by_tile_names(tiles_name, tiles_level, tiles_date)

    if args.command == "download":
        products = []
        tile_name = args.name
        tile_uuid = args.uuid
        products.append((tile_name, tile_uuid))
        outdir = args.outdir
        _download_by_uuid(products, outdir)

    if args.command == "correct":
        indir = args.indir
        _correct_1c_to_2a(indir)


main()
