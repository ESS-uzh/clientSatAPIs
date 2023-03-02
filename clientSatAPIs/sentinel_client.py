from datetime import date
import time
import zipfile

from sentinelsat import SentinelAPI

########################

# Query scihub API for Sentinel2 product

# 1. The query uses tile name and cloud coverage as filters
# 2. The results are written to a file (OUTFILE)

########################


# connect to the API
# A .netrc file with username and password must be present in the home folder
api = SentinelAPI(None, None, "https://scihub.copernicus.eu/dhus")

OUTFILE = "./sent_client.log"
TILES = ["*T20QME*", "*T20QNE*"]
import pdb


def _query_by_tile_names(tiles, date=("20150101", "20170101"), cc=(0,5)):
    for tl in tiles:
        products = api.query(
            platformname="Sentinel-2",
            # processingLevel="Level-2A",
            date=("20150101", "20170101"),
            filename=tl,
            cloudcoverpercentage=(0, 5),
        )
        with open(OUTFILE, "a") as f:
            f.write(f"Tile: {tl}")
            f.write("\n")

            for k in products.keys():
                begin_acquisition_date = products.get(k)["beginposition"].date()
                date = begin_acquisition_date.strftime("%m/%d/%Y")
                size = products.get(k)["size"]
                uuid = products.get(k)["uuid"]
                f.write(f"{date}, {size}, {uuid}\n")

            f.write("\n")
            f.write("\n")

def _download_by_uuid(products, dirpath):

    for name, uuid in products:
        time.sleep(5)
        fzip = '.'.join([name, 'zip'])
        fzippath = os.path.join(dirpath, fzip)
        #logger.info(f'Trying tile name: {tile_db.name}, uuid: {tile_db.uuid}')
        try:
            products = api.download(uuid, dirpath)
            print(f'{name} downloaded')
        except sentinelsat.exceptions.LTATriggered:
            print(f'{uuid} not online, skipped..')
            continue
        except sentinelsat.exceptions.ServerError:
            print(f'Got server error..')
            return
        try:
            logger.info(f'Try to unzip...')
            with zipfile.ZipFile(fzippath, 'r') as zip_ref:
                zip_ref.extractall(dirpath)
        except zipfile.BadZipFile:
            tile_db.update_tile_status('corrupted')
            logger.info(f'update {tile_db.name} as corrupted')
            os.remove(fzippath)
            continue

        os.remove(fzippath)

def _correct_1c_to_2a(indir):
    
    # this works only when run on the dcorr server
    my_env = os.environ.copy()
    my_env['PATH'] = '/home/ubuntu/Sen2Cor-02.08.00-Linux64/bin:' + my_env['PATH']
    my_env['SEN2COR_HOME'] = '/home/ubuntu/sen2cor/2.8'
    my_env['SEN2COR_BIN'] = '/home/ubuntu/Sen2Cor-02.08.00-Linux64/lib/python2.7/site-packages/sen2cor'
    my_env['LC_NUMERIC'] = 'C'
    my_env['GDAL_DATA'] = '/home/ubuntu/Sen2Cor-02.08.00-Linux64/share/gdal'
    my_env['GDAL_DRIVER_PATH']= 'disable'

    # load all tiles fo correction

    for f in fpaths:
        print(f'Start correction for tile {f}')
        # get the full path to tile
        # fpath = os.path.join(full_basedir, tile_db.fname)

        cmd = f'L2A_Process {f}',

        try:
            result = subprocess.check_output(cmd, env=my_env, shell=True)
        except subprocess.CalledProcessError as e:
            logger.error(e.output)
            continue

        print(f'Finished correction for tile {f}')

        #new_fname = [_dir for _dir in os.listdir(full_basedir) if
        #    fnmatch.fnmatch(_dir, f'*_MSIL2A_*_{tile_db.name}_*')][0]

def cli():
    parser = Argparse.ArgumentParser(
            description = "Search, download and correct sentinel2 products"
            )
    subparsers = parser.add_subparsers(required=True)

    # create the parser for the "foo" command
    parser_query = subparsers.add_parser('query', help="query the scihub database")
    parser_query.add_argument('-name', type=str, help="name of the tiles")
    parser_query.add_argument('-date', type=str, help"date range, e.g. yyyyMMdd - yyyyMMdd")
    #parser_query.set_defaults(func=foo)


def main():
    parser = cli()
    args = parser.parse_args()
    print(f"args: {args}")

main()
