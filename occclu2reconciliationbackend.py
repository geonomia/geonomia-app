import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Create skeletal backend table for reconciliation service")
    parser.add_argument("inputfile", help="Path to the input file (tab separated CSV, output of clustering process)")
    parser.add_argument("--source_fields", help="Comma separated list of source fields to concatenate for reconciliation backend key (e.g. recordedby_first_familyname,recordnumber_mainnumber,year)")
    parser.add_argument("--separator", default=' ', help="Separator to use when concatenating source fields for reconciliation backend key (e.g. space)")
    parser.add_argument("--id_col", default='gbifid', help="Column name for the row id (e.g. gbifid)")
    parser.add_argument("--cluster_id_col", default='cluster_stage1_id', help="Column name for the cluster ID (e.g. cluster_stage1_id)")
    parser.add_argument("--destination_id_col", default='gbifid', help="Column name for the ID used for the reconciliation backend key (e.g. gbifid)")
    parser.add_argument("--destination_field", help="Name of the destination field to create for the reconciliation backend key (e.g. reconciliation_backend_key)")
    parser.add_argument("--drop_duplicates", action="store_true", help="Whether to drop duplicate rows based on the destination field after creating the reconciliation backend key")
    parser.add_argument("output_file", help="Path to the output file")

    args = parser.parse_args()

    cols = [args.id_col, args.cluster_id_col] + args.source_fields.split(',')
    if args.destination_id_col not in cols:
        cols.append(args.destination_id_col)
    df = pd.read_csv(args.inputfile, sep='\t', usecols=cols)
    # Only keep rows where the specified source fields are not null, and the cluster ID is not null and not -1
    mask =  (df[args.cluster_id_col].notnull() & 
                (~df[args.cluster_id_col].isin([-1])) )
    for source_field in args.source_fields.split(','):
        mask = (mask & df[source_field].notnull())
    df = df[mask]
    print(f"Loaded {len(df)} rows from {args.inputfile} after filtering for non-null {args.source_fields} and valid {args.cluster_id_col}")
    print(f"Sample rows:\n {df.head()}")

    # We don't want .0 from numeric fields, so any that are float type, convert to Int64 first, coercing errors to NaN, then convert to Int64 again to remove .0, then convert to string
    for source_field in args.source_fields.split(','):
        if pd.api.types.is_float_dtype(df[source_field]):
            df[source_field] = pd.to_numeric(df[source_field], errors='coerce').astype('Int64').astype(str)
    # Create column for use in reconciliation backend, concatenating source fields with specified separator

    df[args.destination_field] = df[args.source_fields.split(',')].agg(args.separator.join, axis=1)

    print(f"Sample rows with reconciliation data:\n {df.head()}")

    if args.drop_duplicates:
        df = df.drop_duplicates(subset=[args.destination_field])

    # Save the output to a new tab separated CSV file with columns: gbifid, reconciliation_backend_key, cluster_stage1_id
    df[[args.destination_id_col, args.destination_field]].to_csv(args.output_file, index=False, sep='\t')

if __name__ == "__main__":
    main()