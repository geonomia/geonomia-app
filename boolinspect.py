import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Explore bool flags in outputs of clustering process")
    parser.add_argument("input_file", help="Path to the output of the clustering process (tab sep CSV)")

    args = parser.parse_args()

    # Load the input file
    df = pd.read_csv(args.input_file, sep='\t')
    print(f"Loaded {len(df)} rows from {args.input_file}")

    eligibility_cols = [col for col in df.columns if col.endswith('_eligible')]
    print(f"Eligibility columns: {eligibility_cols}")
    print(f"Datatypes of columns:\n {df[eligibility_cols].dtypes}")
    for col in eligibility_cols:
        # Set non-True values to False, to make it easier to work with in sqlite
        # define mask to gather true values, treating any value that is not the boolean True as False
        # mask = (df[col] == True)
        # # Update the column to be boolean, with True where the mask is True and False otherwise
        # df[col] = False  # Set all values to False first
        # df.loc[mask, col] = True

        print(f"Distribution of values in column {col}:\n {df[col].value_counts()}")

    print("Inspecting combinations of eligibility flags:")
    print(df.groupby(eligibility_cols).size().reset_index(name='count').sort_values('count', ascending=False))

if __name__ == "__main__":
    main()