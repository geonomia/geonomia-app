# geonomia-datasette

This repository builds a sqlite database from these inputs:

1. A GBIF occurrence download
1. The results of a geonomia clustering process
1. Bionomia claim and profile data.

The process downloads Bionomia claim data from zenodo, separates recordedby and identifiedby claims and filters these for those relevant to the occurrences included in a GBIF download. It also builds a profile datafile of the orcid or wikidata profiles relevant to the fitered claims. The output files are suitable for use as join and lookup tables in a sqlite relational database.

Datasette is configured to provide a reconciliation endpoint.
