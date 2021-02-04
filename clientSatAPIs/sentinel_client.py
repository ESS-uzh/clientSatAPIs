from datetime import date

from sentinelsat import SentinelAPI

########################

# Query scihub API for Sentinel2 product

# 1. The query uses tile name and cloud coverage as filters
# 2. The results are written to a file (OUTFILE)

########################


# connect to the API
# A .netrc file with username and password must be present in the home folder
api = SentinelAPI(None, None, 'https://scihub.copernicus.eu/dhus')

OUTFILE = '/home/diego/work/dev/sent_client.log'
TILES = ['*T20MNA*', '*T20MPA*', '*T20MQA*',
         '*T20MNV*', '*T20MPV*', '*T20MQV*',
         '*T20MNB*', '*T20MPB*', '*T20MQB*']

for tl in TILES:

    products = api.query(platformname='Sentinel-2', filename=tl, cloudcoverpercentage=(0, 1))

    with open(OUTFILE, 'a') as f:
        f.write(f'Tile: {tl}\n')

        for k in products.keys():
            begin_acquisition_date = products.get(k)['beginposition'].date()
            date = begin_acquisition_date.strftime("%m/%d/%Y")
            size = products.get(k)['size']
            uuid = products.get(k)['uuid']
            f.write(f'{date}, {size}, {uuid}\n')

        f.write('\n')
        f.write('\n')
