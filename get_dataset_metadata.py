import argparse
import pandas as pd
from pygbif import registry as reg
import json
from geonomia_dtypes import DATA_SCHEMA
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

licenses = {'http://creativecommons.org/licenses/by-nc/4.0/legalcode':'CC BY-NC 4.0'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("--dataset_col_name", type=str, required=False, default='datasetkey')
    parser.add_argument("outputfile")    

    args = parser.parse_args()
    logger.info(f"Reading input file: {args.inputfile}, looking for dataset column: {args.dataset_col_name}")
    df = pd.read_csv(args.inputfile, sep='\t', usecols=[args.dataset_col_name], dtype=DATA_SCHEMA)
    # Get unique dataset keys
    mask  = df[args.dataset_col_name].notnull()
    df = df[mask]
    dataset_keys = df[args.dataset_col_name].unique().tolist()
    logger.info(f"Found {len(dataset_keys)} unique dataset keys in the input file.")
    logger.info("Fetching metadata for each dataset key from GBIF registry.")
    
    dataset_metadata_list = []
    for dataset_key in dataset_keys:
        dataset_metadata = dict()
        dataset_metadata['datasetkey'] = dataset_key
        try:
            gbif_metadata = reg.datasets(uuid=dataset_key)
        except Exception as e:
            logger.error(f"Error fetching metadata for dataset key {dataset_key}: {e}")
            # append the minimal metadata with just the dataset key and continue
            dataset_metadata_list.append(dataset_metadata)
            continue
        license_url = gbif_metadata['license']
        # If the license URL is in our licenses dictionary, add the license and license_url to the dataset metadata
        if license_url in licenses:
            dataset_metadata['license'] = licenses[license_url]
            dataset_metadata['license_url'] = license_url
        dataset_metadata['source_url'] = 'https://doi.org/{}'.format(gbif_metadata['doi'])
        dataset_metadata['name'] = gbif_metadata['title']
        dataset_metadata_list.append(dataset_metadata)

    # Make a pandas DataFrame from the dataset metadata dictionary
    df_datasets = pd.DataFrame(dataset_metadata_list)

    # Write it to our output file as TSV
    logger.info(f"Writing dataset metadata to output file: {args.outputfile}")
    df_datasets.to_csv(args.outputfile, index=False, header=True, sep='\t')

if __name__ == '__main__':
    main()