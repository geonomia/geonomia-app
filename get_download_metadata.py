import argparse
from pygbif import occurrences as occ
import json

licenses = {'http://creativecommons.org/licenses/by-nc/4.0/legalcode':'CC BY-NC 4.0'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("--download_id", type=str)
    parser.add_argument("--dbname", type=str)
    parser.add_argument("outputfile")    

    args = parser.parse_args()

    datasette_metadata = None
    with open(args.inputfile, 'r') as f_in:
        datasette_metadata = json.load(f_in)
 
    gbif_metadata = occ.download_meta(key = args.download_id)
    license_url = gbif_metadata['license']
    if license_url in licenses:
        datasette_metadata['license'] = licenses[license_url]
        datasette_metadata['license_url'] = license_url
    datasette_metadata['source_url'] = 'https://doi.org/{}'.format(gbif_metadata['doi'])

    datasette_metadata_json = json.dumps(datasette_metadata, indent=4)
    with open(args.outputfile, 'w') as f_out:
        f_out.write(datasette_metadata_json)