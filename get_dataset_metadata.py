import argparse
import pandas as pd
from pygbif import registry as reg
import json

licenses = {'http://creativecommons.org/licenses/by-nc/4.0/legalcode':'CC BY-NC 4.0'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("--dataset_col_name", type=str, required=False, default='datasetkey')
    parser.add_argument("outputfile")    

    args = parser.parse_args()

    df = pd.read_csv(args.inputfile, sep='\t', usecols=[args.dataset_col_name])
    # Get unique dataset keys
    dataset_keys = df[args.dataset_col_name].unique().tolist()

    dataset_metadata = dict()

    for dataset_key in dataset_keys:
        dataset_metadata['datasetkey'] = dataset_key
        gbif_metadata = reg.dataset(dataset_key)
        license_url = gbif_metadata['license']
        # If the license URL is in our licenses dictionary, add the license and license_url to the dataset metadata
        if license_url in licenses:
            dataset_metadata['license'] = licenses[license_url]
            dataset_metadata['license_url'] = license_url
        dataset_metadata['source_url'] = 'https://doi.org/{}'.format(gbif_metadata['doi'])
        dataset_metadata['name'] = gbif_metadata['title']

    # Make a pandas DataFrame from the dataset metadata dictionary
    df_datasets = pd.DataFrame([dataset_metadata])

    # Write it to our output file as TSV
    df_datasets.to_csv(args.outputfile, index=False, header=True, sep='\t')

if __name__ == '__main__':
    main()