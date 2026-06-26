import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("--cluster_col_name", type=str, required=False, default='cluster_stage1_id')
    parser.add_argument("--is_primary_key", action='store_true', help="If set, the specified cluster column will be treated as a primary key and we will warn about NaN values.")
    parser.add_argument("outputfile")    

    args = parser.parse_args()

    df = pd.read_csv(args.inputfile, sep='\t')
    # Convert the cluster_col_name column to Int64 type, replacing any non-numeric values with NaN
    df[args.cluster_col_name] = pd.to_numeric(df[args.cluster_col_name], errors='coerce').astype('Int64')
    # Warn about any remaining NaN values if the column is a primary key
    if args.is_primary_key and df[args.cluster_col_name].isnull().any():
        print(f"Warning: The column '{args.cluster_col_name}' contains NaN values.")
    # Write the modified DataFrame to the output file
    df.to_csv(args.outputfile, sep='\t', index=False)

if __name__ == '__main__':
    main()