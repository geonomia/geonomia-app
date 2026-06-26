import pandas as pd
import argparse
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    argparser = argparse.ArgumentParser(description="Add Bionomia profile IDs to occurrence records based on filtered claims with family name agreement")
    argparser.add_argument("occ_file", help="Path to the occurrence file (CSV) with gbifid column")
    argparser.add_argument("claims_file", help="Path to the filtered claims file (CSV) with Subject, Predicate, Object columns")
    argparser.add_argument("output_file", help="Path to the output file (CSV) with added profile IDs")
    args = argparser.parse_args()

    # Load the occurrence file
    df_occ = pd.read_csv(args.occ_file, sep='\t', engine='python', on_bad_lines='skip')
    logger.info(f"Loaded {len(df_occ)} occurrences from {args.occ_file}")

    # Load the filtered claims
    df_claims = pd.read_csv(args.claims_file, sep='\t', engine='python', on_bad_lines='skip')
    logger.info(f"Loaded {len(df_claims)} filtered claims from {args.claims_file}")

    # It is possible to have multiple claims for the same occurrence, and for these multiple claims to be 
    # for different profiles with the same family name, so we will eliminate these from our port for now
    # (alt would be to keep the first or to hold multiple profile ids in a list, but that would be more complex to handle downstream)
    subject_counts = df_claims[df_claims.family_name_agreement]['Subject'].value_counts()
    logger.info(f"Found {len(subject_counts)} unique subjects in claims")
    # How many subjects have more than one claim?
    multiple_claims_subjects = subject_counts[subject_counts > 1]
    single_claims_subjects = subject_counts[subject_counts == 1]
    logger.info(f"Found {len(multiple_claims_subjects)} subjects with multiple claims, disregarding these for now")
    logger.info(f"Found {len(single_claims_subjects)} subjects with single claims")

    # Perform the join operation
    df_result = pd.merge(df_occ, df_claims[df_claims.Subject.isin(single_claims_subjects.index)][['Subject','Object']], left_on="gbifid", right_on="Subject", how="left")
    logger.info(f"Merged data: {len(df_result)} records")

    # Rename the 'Object' column to 'bionomia_profile_id' for clarity
    logger.info("Renaming 'Object' column to 'bionomia_profile_id'")
    df_result.rename(columns={'Object': 'bionomia_profile_id'}, inplace=True)

    # Save the result
    df_result.to_csv(args.output_file, sep='\t', index=False)
    logger.info(f"Results saved to {args.output_file}")

if __name__ == "__main__":  
    main()