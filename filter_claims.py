import argparse
import pandas as pd
from nameutils import familyNamesAgree

def main():
    parser = argparse.ArgumentParser(description="Filter a bionomia claims file based on occurrence ids from a gbif download")
    parser.add_argument("claims_file", help="Path to the bionomia claims file (gzipped CSV)")
    parser.add_argument("occurrence_file", help="Path to the tab delimited GBIF download file containing occurrence ids  in the gbifid column")
    parser.add_argument("profiles_file", help="Path to the bionomia profiles file (CSV)")
    parser.add_argument("output_file", help="Path to the output file for filtered claims (gzipped CSV)")

    args = parser.parse_args()

    # Load the claims file
    df_claims = pd.read_csv(args.claims_file, compression='gzip')
    print(f"Loaded {len(df_claims)} claims from {args.claims_file}")
    print(f"Sample claims:\n {df_claims.head()}")
    ## Remove the 'https://gbif.org/occurrence/' prefix from the 'Subject' column to get the occurrence ids
    #df_claims['occurrence_id'] = df_claims['Subject'].str.replace('https://gbif.org/occurrence/', '', regex=False)
    ## convert occurrence_id to Int64, coercing errors to NaN
    #df_claims['occurrence_id'] = pd.to_numeric(df_claims['occurrence_id'], errors='coerce')

    # Load the occurrence ids
    df_occ = pd.read_csv(args.occurrence_file, sep='\t', usecols=['gbifid','recordedby_first_familyname'])
    df_occ['gbifid'] = pd.to_numeric(df_occ['gbifid'], errors='coerce')

    print(f"Loaded {len(df_occ)} occurrence ids from {args.occurrence_file}")
    print(f"Sample occurrence ids in occurrence file: {df_occ['gbifid'].head()}")
    # Filter the claims based on occurrence ids
    df_claims_filtered = df_claims[df_claims['Subject'].isin(df_occ['gbifid'])]
    print(f"Filtered down to {len(df_claims_filtered)} claims after matching occurrence ids")

    # Now also check on agreement between the recordedby_first_familyname in the occurrence file and the Family name in the profiles file, for claims that have a matching occurrence id, to further filter the claims to those that are more likely to be correct
    df_profiles = pd.read_csv(args.profiles_file, sep=',')
    print(f"Loaded {len(df_profiles)} profiles from {args.profiles_file}")
    print(f"Sample profiles:\n {df_profiles.head()}")
    print(df_profiles.sample(n=1).T)

    # Make an Object column taking data first from ORCID column and then from wikidata column, to allow joining with the claims file on the Object column
    df_profiles['Object'] = df_profiles['ORCID'].combine_first(df_profiles['wikidata'])

    df_claims_filtered = df_claims_filtered.merge(df_occ, left_on='Subject', right_on='gbifid', how='left').merge(df_profiles, left_on='Object', right_on='Object', how='left')
    print(f"Claims merged with occurrences and profiles has {len(df_claims_filtered)} rows and {len(df_claims_filtered.columns)} columns")
    print(f"Sample claims merged with occurrences and profiles:\n {df_claims_filtered.head()}")

    # Add flag column to indicate whether the recordedby_first_familyname in the occurrence file matches the Family name in the profiles file, using the familyNamesAgree function to check for agreement
    df_claims_filtered['family_name_agreement'] = df_claims_filtered.apply(lambda row: familyNamesAgree(row['recordedby_first_familyname'], row['Family']), axis=1)
    
    print(f"Claims with family name agreement:\n {df_claims_filtered[df_claims_filtered['family_name_agreement']].head()}")     


    # Save the filtered claims to a new gzipped CSV file
    output_columns = ['Subject', 'Predicate', 'Object']  
    df_claims_filtered[df_claims_filtered['family_name_agreement']][output_columns].to_csv(args.output_file, index=False, sep='\t')

if __name__ == "__main__":
    main()
