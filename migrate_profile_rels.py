import argparse
import pandas as pd
from nameutils import familyNamesAgree

# Show 250 rows and all columns in pandas output
pd.set_option('display.max_rows', 250)
pd.set_option('display.max_columns', None)
# Set display width to 1000 characters to avoid line breaks in output
pd.set_option('display.width', 1000)

def main():
    parser = argparse.ArgumentParser(description="Migrate profile rels from occ level to cluster level, checking on coherence btw profile family name and recordedby first familyname")
    parser.add_argument("claims_file", help="Path to the bionomia claims file (gzipped CSV)")
    parser.add_argument("profiles_file", help="Path to the bionomia profiles file (CSV)")
    parser.add_argument("occ_file", help="Path to the labelled occurrence file (CSV)")
    parser.add_argument("clu_file", help="Path to the cluster file (CSV)")
    parser.add_argument("output_file", help="Path to the output file for the cluster to profile mapping (CSV)")

    args = parser.parse_args()

    # Load the claims file
    df_claims = pd.read_csv(args.claims_file, sep='\t')
    print(f"Loaded {len(df_claims)} claims from {args.claims_file}")
    print(f"Sample claims:\n {df_claims.head()}")
    print(df_claims.sample(n=1).T)

    # Load the occ file
    df_occ = pd.read_csv(args.occ_file, sep='\t', usecols=['gbifid', 'recordedby_first_familyname', 'cluster_stage1_id'], engine='python', on_bad_lines='skip')
    print(f"Loaded {len(df_occ)} occurrences from {args.occ_file}")
    print(f"Sample occurrences:\n {df_occ.head()}")
    print(df_occ.sample(n=1).T)

    df_claim_occ = df_claims.merge(df_occ, left_on='Subject', right_on='gbifid', how='left')
    print(f"Claims merged with occurrences has {len(df_claim_occ)} rows and {len(df_claim_occ.columns)} columns")
    print(f"Sample claims merged with occurrences:\n {df_claim_occ.head()}")
    print(df_claim_occ.sample(n=1).T)

    df_profile = pd.read_csv(args.profiles_file, sep='\t')
    print(f"Loaded {len(df_profile)} profiles from {args.profiles_file}")
    print(f"Sample profiles:\n {df_profile.head()}")
    print(df_profile.sample(n=1).T)

    df_claim_occ = df_claim_occ.merge(df_profile, left_on='Object', right_on='Object', how='left')
    print(f"Claims merged with occurrences and profiles has {len(df_claim_occ)} rows and {len(df_claim_occ.columns)} columns")
    print(f"Sample claims merged with occurrences and profiles:\n {df_claim_occ.head()}")
    print(df_claim_occ.sample(n=1).T)

    mask = df_claim_occ['recordedby_first_familyname'].notnull() & df_claim_occ['cluster_stage1_id'].notnull() & (~df_claim_occ['cluster_stage1_id'].isin([-1]))
    print(df_claim_occ[mask].groupby(['Object','Family','Given']).agg({'cluster_stage1_id': 'nunique','gbifid': 'nunique','recordedby_first_familyname':'unique'}))

    # mask = mask & (df_claim_occ['recordedby_first_familyname'] != df_claim_occ['Family'])
    # print(df_claim_occ[mask].groupby(['Object','Family','Given']).agg({'cluster_stage1_id': 'nunique','gbifid': 'nunique','recordedby_first_familyname':'unique'}))

    # Group df_claim_occ by cluster_stage1_id, retaining only those clusters with: 
    # exactly one unique profile (Object) 
    # one unique recordedby_first_familyname
    # where the recordedby_first_familyname is the same as the profile Family name
    # and create a new dataframe with columns: 
    # cluster_stage1_id, Object, Family, Given, recordedby_first_familyname
    df_clu_profile = df_claim_occ[mask].groupby('cluster_stage1_id').filter(lambda x: x['Object'].nunique() == 1 and x['recordedby_first_familyname'].nunique() == 1 and familyNamesAgree(x['recordedby_first_familyname'].iloc[0], x['Family'].iloc[0])).groupby('cluster_stage1_id').agg({'Object': 'first', 'Family': 'first', 'Given': 'first', 'recordedby_first_familyname': 'first'}).reset_index()
    print(f"Cluster to profile mapping has {len(df_clu_profile)} rows and {len(df_clu_profile.columns)} columns")
    print(f"Cluster to profile mapping contains {df_clu_profile['Object'].nunique()} unique profiles and {df_clu_profile['cluster_stage1_id'].nunique()} unique cluster ids")
    print(f"Sample cluster to profile mapping:\n {df_clu_profile.head()}")
    print(df_clu_profile.sample(n=1).T)

    # Show the clusters that have multiple profiles mapping to them, and the profiles that map to multiple clusters, to check on coherence of the mapping
    df_clu_profile_multi = df_claim_occ[mask].groupby('cluster_stage1_id').filter(lambda x: x['Object'].nunique() > 1 or x['recordedby_first_familyname'].nunique() > 1 or not familyNamesAgree(x['recordedby_first_familyname'].iloc[0], x['Family'].iloc[0])).groupby('cluster_stage1_id').agg({'Object': lambda x: list(x.unique()), 'Family': lambda x: list(x.unique()), 'Given': lambda x: list(x.unique()), 'recordedby_first_familyname': lambda x: list(x.unique())}).reset_index()
    print(f"Clusters with multiple profiles or mismatched family names has {len(df_clu_profile_multi)} rows and {len(df_clu_profile_multi.columns)} columns")
    print(f"Sample clusters with multiple profiles or mismatched family names:\n {df_clu_profile_multi}")
    print(df_clu_profile_multi.sample(n=1).T)

    # Make map of cluster_stage1_id to profile Object
    clu_profile_map = df_clu_profile.set_index('cluster_stage1_id')['Object'].to_dict()
    print(f"Cluster to profile map contains {len(clu_profile_map)} entries")

    df_clu = pd.read_csv(args.clu_file, sep='\t')
    print(f"Loaded {len(df_clu)} clusters from {args.clu_file}")    
    print(f"Sample clusters:\n {df_clu.head()}")
    print(df_clu.sample(n=1).T)
    # Add profile ID column to cluster file based on the cluster_stage1_id to profile Object map
    df_clu['profile_Object'] = df_clu['cluster_stage1_id'].map(clu_profile_map)
    print(f"Clusters with profile mapping has {len(df_clu)} rows and {len(df_clu.columns)} columns")
    print(f"Sample clusters with profile mapping:\n {df_clu.head()}")

    df_clu.to_csv(args.output_file, index=False, sep='\t')
    
if __name__ == "__main__":
    main()
