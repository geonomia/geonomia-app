import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Join original occurrence download and output of clustering process to create a labelled occurrence data file suitable for insert into sqlite")
    parser.add_argument("occ_file", help="Path to the downloaded occurrence file (gzipped TSV)")
    parser.add_argument("occ_clustered_file", help="Path to the clustered occurrence file (TSV)")
    parser.add_argument("output_file", help="Path to the output file for the joined data (TSV)")
    parser.add_argument("--id_col_name", default="gbifid", help="Name of the column containing the occurrence id in both files (default: 'gbifid')")

    args = parser.parse_args()

    df_occ = pd.read_csv(args.occ_file, sep='\t', compression='zip', on_bad_lines="skip",low_memory=False)
    print(f"Loaded {len(df_occ)} occurrences from {args.occ_file}")
    print(f"Columns in occurrence file: {df_occ.columns.tolist()}")
    eligibility_columns = [col for col in df_occ.columns if col.endswith('_eligible')]
    print(f"Eligibility columns in occ file: {eligibility_columns}")
    for col in eligibility_columns:
        # Set non-True values to False, to make it easier to work with in sqlite
        df_occ[col] = df_occ[col].map({'True': True}).fillna(False).astype('bool')
    
    df_occ_clustered = pd.read_csv(args.occ_clustered_file, sep='\t',low_memory=False)
    print(f"Loaded {len(df_occ_clustered)} clustered occurrences from {args.occ_clustered_file}")
    print(f"Columns in clustered file: {df_occ_clustered.columns.tolist()}")
    eligibility_columns = [col for col in df_occ_clustered.columns if col.endswith('_eligible')]
    print(f"Eligibility columns in clustered file: {eligibility_columns}")
    for col in eligibility_columns:
        # Set non-True values to False, to make it easier to work with in sqlite
        #  df_occ_clustered[col] = df_occ_clustered[col].map({'True': True}).fillna(False).astype('bool')
        print(f"Distribution of values in column {col}:\n {df_occ_clustered[col].value_counts(dropna=False)}")

    print(df_occ_clustered.groupby(eligibility_columns).size().reset_index(name='count').sort_values('count', ascending=False))
    
    # We don't want to do a full join as the clustered file is a subset of the 
    # original, so we inspect the columns in the clustered file and only carry 
    # across those not in the original file, to avoid creating duplicate columns
    # for the original data
    # We also need the id column in the clustered file to do the join, so we include that too
    columns_to_add = [args.id_col_name] + [col for col in df_occ_clustered.columns if col not in df_occ.columns]
    print(f"Columns to add from clustered file: {columns_to_add}")

    # Join the clustered data with the original data
    df_joined = df_occ.merge(df_occ_clustered[columns_to_add], left_on=args.id_col_name, right_on=args.id_col_name, how='left')
    print(f"Joined data has {len(df_joined)} rows and {len(df_joined.columns)} columns")
    print(f"Columns in joined data: {df_joined.columns.tolist()}")
    print(f"Sample joined data:\n {df_joined.head()}")
    
    # Modify eligibility columns
    print("Inspecting eligibility columns:")
    for col in eligibility_columns:
        print(f"distribution of values in column {col}:\n {df_joined[col].value_counts(dropna=False)}")
        # print(f"pre-conversion distribution of values in column {col}:\n {df_joined[col].value_counts(dropna=False)}")
        # df_joined[col] = df_joined[col].map({'True': True, 'False': False}).astype(pd.BooleanDtype())
        # print(f"post-conversion distribution of values in column {col}:\n {df_joined[col].value_counts(dropna=False)}")

    # Modify boolean columns to be 1 for True and 0 for False, to make it easier to work with in sqlite
    print(df_joined.dtypes)
    bool_cols = df_joined.select_dtypes(include=['bool','boolean']).columns
    print(f"Boolean columns to convert: {bool_cols}")
    for col in bool_cols:
        print(f"Converting column {col} to integer")
        print(f"pre-conversion distribution of values in column {col}:\n {df_joined[col].value_counts(dropna=False)}")
        df_joined[col] = df_joined[col].map({True: 1, False: 0}).astype('Int64')
        print(f"post-conversion distribution of values in column {col}:\n {df_joined[col].value_counts(dropna=False)}")
    # df_joined[bool_cols] = df_joined[bool_cols].astype(int)

    # Display group by eligibility_columns to check the distribution of eligible vs ineligible occurrences
    for col in eligibility_columns:
        print(df_joined[col].describe())

    print("Distribution of eligible vs ineligible occurrences:")
    print(df_joined.groupby(eligibility_columns).size().reset_index(name='count'))

    # Save the joined data to a new TSV file
    df_joined.to_csv(args.output_file, sep='\t', index=False)

if __name__ == "__main__":
    main()