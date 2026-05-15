import argparse
import pandas as pd
import requests

def get_orcid_details(orcid_id):
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/person"
    headers = {
        "Accept": "application/json"
    }

    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()

    data = r.json()

    # # Pretty print the data for debugging
    # print(f"Data for ORCID {orcid_id}:\n {json.dumps(data, indent=2)}")

    details = [None, None]  # Placeholder for Family Name, Given Name
    for i, key in enumerate(['family-name', 'given-names']):
        if data.get("name", {}).get(key):
             details[i] = data["name"][key]["value"]
    
    # # Try to get biography content if available
    # try:
    #     if data.get("biography", {}).get("content"):
    #         details[-1] = data["biography"]["content"]
    # except:
    #     pass

    return tuple(details)

def main():
    parser = argparse.ArgumentParser(description="Filter bionomia profiles relevant to a bionomia claims file")
    parser.add_argument("claims_file", help="Path to the bionomia claims file (gzipped CSV)")
    parser.add_argument("profiles_file", help="Path to the bionomia profiles file (CSV)")
    parser.add_argument("output_file", help="Path to the output file for filtered profiles (CSV)")

    args = parser.parse_args()

    # Load the claims file
    df_claims = pd.read_csv(args.claims_file, sep='\t')
    print(f"Loaded {len(df_claims)} claims from {args.claims_file}")
    print(f"Sample claims:\n {df_claims.head()}")

    # Load the profiles file
    df_profiles = pd.read_csv(args.profiles_file)
    print(f"Loaded {len(df_profiles)} profiles from {args.profiles_file}")
    print(f"Sample profiles:\n {df_profiles.head()}")

    print(f"Sample profiles (ORCID):\n {df_profiles[df_profiles['ORCID'].notnull()].head()}")
    print(f"Sample profiles (wikidata):\n {df_profiles[df_profiles['wikidata'].notnull()].head()}")

    # Separate claims with wikidata and ORCID identifiers in the Object column
    mask_wikidata = df_claims['Object'].str.startswith('Q')
    df_named_claims_wikidata = df_claims[mask_wikidata].join(df_profiles.set_index('wikidata'), on=df_claims[mask_wikidata]['Object'])
    df_named_claims_orcid = df_claims[~mask_wikidata].join(df_profiles.set_index('ORCID'), on=df_claims[~mask_wikidata]['Object'])
    # Concatenate the named claims back together
    df_named_claims = pd.concat([df_named_claims_wikidata, df_named_claims_orcid], ignore_index=True)

    # Find any ORCID labelled profiles that lack Family / Name information
    mask_orcid = df_named_claims['Object'].str.match(r'^[0-9X]{4}-[0-9X]{4}-[0-9X]{4}-[0-9X]{4}$')
    mask_missing_name = df_named_claims['Family'].isnull() | df_named_claims['Given'].isnull()
    missing_name_orcids = df_named_claims[mask_orcid & mask_missing_name]['Object'].unique()
    print(f"{len(missing_name_orcids)} ORCID profiles with missing name or family information:\n {missing_name_orcids}")

    orcid_map = {}
    for orcid in missing_name_orcids:  
        orcid_map[orcid] = get_orcid_details(orcid)
    for key, details in orcid_map.items():
        print(f"ORCID: {key}, details: {details}")

    # Make a temp column to hold orcid details tuple
    df_named_claims['orcid_details'] = df_named_claims['Object'].map(orcid_map)
    # Update the Family and Given columns with the details from ORCID where available
    df_named_claims['Family'] = df_named_claims.apply(lambda row: row['orcid_details'][0] if pd.isnull(row['Family']) and pd.notnull(row['orcid_details']) else row['Family'], axis=1)
    df_named_claims['Given'] = df_named_claims.apply(lambda row: row['orcid_details'][1] if pd.isnull(row['Given']) and pd.notnull(row['orcid_details']) else row['Given'], axis=1)

    print(f"Named claims:\n {df_named_claims.head()}")

    # Show number of claims per family name
    print("Number of claims per family name:")
    print(df_named_claims['Family'].value_counts().head(20))

    print("Alan Paton's claims:")
    print(df_named_claims[df_named_claims['Object'].isin(['0000-0002-6052-6675'])].head(20))

    df_named_claims[['Object','Family','Given']].drop_duplicates().to_csv(args.output_file, index=False, sep='\t')

if __name__ == "__main__":
    main()