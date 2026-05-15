import re
import pandas as pd

def familyNamesAgree(family1, family2):
    names_agree = False
    if pd.isnull(family1) or pd.isnull(family2):
        return names_agree
    names_agree = family1.strip().lower() == family2.strip().lower()
    if not names_agree:
        # Check if one name is contained within the other as a complete word (e.g. "Smith" in "Smith-Jones")
        # use regex to split the family names into words, and check if any word in one family name matches the other family name
        family1_words = set(re.split(r'[-\s]+', family1.strip().lower()))
        family2_words = set(re.split(r'[-\s]+', family2.strip().lower() ))
        names_agree = bool(family1_words & family2_words)
    return names_agree
