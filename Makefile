# Requires environment variable GBIF_DOWNLOAD_ID
# As geonomia projects are defined using countrycode, we also use a 
# GBIF_DOWNLOAD_COUNTRYCODE environment variable to clustered files 
# (built in a sibling project) and to filter claims to those relevant 
# to the country. 
# e.g. occurrences-prepared-COUNTRYCODE.tsv
bionomia_public_claims_download_url = https://zenodo.org/records/19363546/files/bionomia-public-claims.csv.gz?download=1

SHARED_DIR 			?=../geonomia-shared

DOWNLOAD_DIR  		:= downloads
DOWNLOAD_DIR_SHARED := $(SHARED_DIR)/downloads

DATA_DIR 			:= data
DATA_DIR_SHARED 	:= $(SHARED_DIR)/data

OCC_FILE_ZIP := $(DOWNLOAD_DIR_SHARED)/occurrences-$(GBIF_DOWNLOAD_COUNTRYCODE).zip
OCC_FILE_TSV := $(DATA_DIR_SHARED)/occurrences-$(GBIF_DOWNLOAD_COUNTRYCODE).tsv
OCC_CLUSTERED_SHARED_FILE := $(OCC_FILE_TSV)
OCC_CLUSTERED_FILE := $(DATA_DIR)/occurrences-$(GBIF_DOWNLOAD_COUNTRYCODE)-clustered-for-insert.tsv
OCC_SUMMARY_SHARED_FILE := $(DATA_DIR_SHARED)/trip_cluster_summary.txt
OCC_SUMMARY_FILE := $(DATA_DIR)/trip_cluster_summary-for-insert.txt
OCC_SUMMARY_W_PROFILES_FILE := $(DATA_DIR_SHARED)/occurrences-$(GBIF_DOWNLOAD_COUNTRYCODE)-clustered-stage1-summary-w-profiles.tsv
OCC_WITH_PROFILES_FILE := $(DATA_DIR_SHARED)/occurrences-$(GBIF_DOWNLOAD_COUNTRYCODE)-clustered-with-profiles.tsv
#.PRECIOUS: $(OCC_FILE_TSV)

echo:
	@echo "GBIF_DOWNLOAD_COUNTRYCODE is set to: $(GBIF_DOWNLOAD_COUNTRYCODE)"
	@echo "This will be used to download and process occurrence data for the specified country code."
	@echo "Make sure to set GBIF_DOWNLOAD_COUNTRYCODE environment variable before running the make commands."	
	@echo "OCC_FILE_ZIP is set to: $(OCC_FILE_ZIP)"
	@echo "OCC_FILE_TSV is set to: $(OCC_FILE_TSV)"
	@echo "OCC_CLUSTERED_FILE is set to: $(OCC_CLUSTERED_FILE)"
	@echo "OCC_SUMMARY_FILE is set to: $(OCC_SUMMARY_FILE)"
	@echo "OCC_SUMMARY_W_PROFILES_FILE is set to: $(OCC_SUMMARY_W_PROFILES_FILE)"
	$(PIP) list

VENV_DIR      := .venv
VENV_SENTINEL := $(VENV_DIR)/.installed

ifeq ($(OS),Windows_NT)
VENV_BIN      := $(VENV_DIR)/Scripts
SYSTEM_PYTHON ?= python
PYTHON        := $(VENV_BIN)/python.exe
PIP           := $(VENV_BIN)/pip.exe
SQLITE_UTILS  := $(VENV_BIN)/sqlite-utils.exe
DATASETTE     := $(VENV_BIN)/datasette.exe

else
VENV_BIN      := $(VENV_DIR)/bin
SYSTEM_PYTHON ?= python3
PYTHON        := $(VENV_BIN)/python
PIP           := $(VENV_BIN)/pip
SQLITE_UTILS  := $(VENV_BIN)/sqlite-utils
DATASETTE     := $(VENV_BIN)/datasette
endif

## Create virtualenv and install dependencies
$(VENV_SENTINEL): requirements.txt
	$(SYSTEM_PYTHON) -m venv $(VENV_DIR)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	touch $(VENV_SENTINEL)

install: $(VENV_SENTINEL)

# Fix problem with float ids in CSV files by converting them to integers
$(OCC_CLUSTERED_FILE): $(VENV_SENTINEL) fix_cluster_ids.py $(OCC_CLUSTERED_SHARED_FILE)
	mkdir -p $(DATA_DIR)
	$(PYTHON) fix_cluster_ids.py $(OCC_CLUSTERED_SHARED_FILE) $@

$(OCC_SUMMARY_FILE): $(VENV_SENTINEL) fix_cluster_ids.py $(OCC_SUMMARY_SHARED_FILE)
	mkdir -p $(DATA_DIR)
	$(PYTHON) fix_cluster_ids.py --is_primary_key $(OCC_SUMMARY_SHARED_FILE) $@

## Download Bionomia claims 
$(DOWNLOAD_DIR)/bionomia_public_claims.csv.gz: 
	mkdir -p $(DOWNLOAD_DIR)
	wget -q -O $@ ${bionomia_public_claims_download_url}

# Download bionomia profiles
$(DOWNLOAD_DIR)/bionomia-public-profiles.csv: 
	mkdir -p $(DOWNLOAD_DIR)
	wget -q -O $@ https://bionomia.net/data/bionomia-public-profiles.csv

$(DATA_DIR)/bionomia_public_claims_recordedby.csv.gz: $(DOWNLOAD_DIR)/bionomia_public_claims.csv.gz
	mkdir -p $(DATA_DIR)
	# Extract header and rows where the second column contains "recordedBy"
	# Also execute string replacements: 
	# 	Remove 'https://gbif.org/occurrence/' from the first column
	# 	Remove 'http://rs.tdwg.org/dwc/iri/' from the second column
	# 	Remove 'https://orcid.org/' and 'http://www.wikidata.org/entity/' from the third column
	zcat $< | awk -F',' 'NR == 1 || $$2 ~ /recordedBy/' | sed 's/https:\/\/gbif.org\/occurrence\///g' | sed 's/http:\/\/rs.tdwg.org\/dwc\/iri\///g' | sed 's/https:\/\/orcid.org\///g' | sed 's/http:\/\/www.wikidata.org\/entity\///g' | gzip -c > $@

$(DATA_DIR)/bionomia_public_claims_identifiedby.csv.gz: $(DOWNLOAD_DIR)/bionomia_public_claims.csv.gz
	mkdir -p $(DATA_DIR)
	# Extract header and rows where the second column contains "identifiedBy"
	# Also execute string replacements: 
	# 	Remove 'https://gbif.org/occurrence/' from the first column
	# 	Remove 'http://rs.tdwg.org/dwc/iri/' from the second column
	# 	Remove 'https://orcid.org/' and 'http://www.wikidata.org/entity/' from the third column
	zcat $< | awk -F',' 'NR == 1 || $$2 ~ /identifiedBy/' | sed 's/https:\/\/gbif.org\/occurrence\///g' | sed 's/http:\/\/rs.tdwg.org\/dwc\/iri\///g' | sed 's/https:\/\/orcid.org\///g' | sed 's/http:\/\/www.wikidata.org\/entity\///g' | gzip -c > $@

BIONOMIA_CLAIMS_RB_CSV_GZ := $(DATA_DIR)/bionomia_public_claims_recordedby.csv.gz
BIONOMIA_CLAIMS_IB_CSV_GZ := $(DATA_DIR)/bionomia_public_claims_identifiedby.csv.gz

BIONOMIA_CLAIMS_RB_FILTERED_CSV_GZ := $(DATA_DIR)/bionomia_public_claims_recordedby_filtered-$(GBIF_DOWNLOAD_COUNTRYCODE).csv.gz 
BIONOMIA_CLAIMS_RB_FILTERED_CSV := $(DATA_DIR)/bionomia_public_claims_recordedby_filtered-$(GBIF_DOWNLOAD_COUNTRYCODE).csv 

BIONOMIA_CLAIMS_IB_FILTERED_CSV_GZ := $(DATA_DIR)/bionomia_public_claims_identifiedby_filtered-$(GBIF_DOWNLOAD_COUNTRYCODE).csv.gz 
BIONOMIA_CLAIMS_IB_FILTERED_CSV := $(DATA_DIR)/bionomia_public_claims_identifiedby_filtered-$(GBIF_DOWNLOAD_COUNTRYCODE).csv 

BIONOMIA_PROFILES_FILTERED_CSV_GZ := $(DATA_DIR)/bionomia_profiles_filtered-$(GBIF_DOWNLOAD_COUNTRYCODE).csv.gz
BIONOMIA_PROFILES_FILTERED_CSV := $(DATA_DIR)/bionomia_profiles_filtered-$(GBIF_DOWNLOAD_COUNTRYCODE).csv

$(BIONOMIA_CLAIMS_RB_FILTERED_CSV): $(VENV_SENTINEL) filter_claims.py $(BIONOMIA_CLAIMS_RB_CSV_GZ) $(OCC_CLUSTERED_FILE) $(DOWNLOAD_DIR)/bionomia-public-profiles.csv
	mkdir -p $(DATA_DIR)
	$(PYTHON) filter_claims.py $(BIONOMIA_CLAIMS_RB_CSV_GZ) $(OCC_CLUSTERED_FILE) $(DOWNLOAD_DIR)/bionomia-public-profiles.csv $@

filter_claims_rb: $(BIONOMIA_CLAIMS_RB_FILTERED_CSV)
filter_claims_ib: $(BIONOMIA_CLAIMS_IB_FILTERED_CSV)

filter_claims: filter_claims_rb filter_claims_ib

$(BIONOMIA_CLAIMS_IB_FILTERED_CSV_GZ): $(VENV_SENTINEL) filter_claims.py $(BIONOMIA_CLAIMS_IB_CSV_GZ) $(OCC_FILE_ZIP)
	mkdir -p $(DATA_DIR)
	$(PYTHON) filter_claims.py $(BIONOMIA_CLAIMS_IB_CSV_GZ) $(OCC_FILE_ZIP) $@

$(BIONOMIA_PROFILES_FILTERED_CSV): $(VENV_SENTINEL) filter_profiles.py $(BIONOMIA_CLAIMS_RB_FILTERED_CSV) $(DOWNLOAD_DIR)/bionomia-public-profiles.csv
	$(PYTHON) filter_profiles.py $(BIONOMIA_CLAIMS_RB_FILTERED_CSV) $(DOWNLOAD_DIR)/bionomia-public-profiles.csv $@

filter_profiles: $(BIONOMIA_PROFILES_FILTERED_CSV)

$(OCC_WITH_PROFILES_FILE): $(VENV_SENTINEL) add_bionomia_to_occ.py $(OCC_CLUSTERED_FILE) $(BIONOMIA_CLAIMS_RB_FILTERED_CSV)
	$(PYTHON) add_bionomia_to_occ.py $(OCC_CLUSTERED_FILE) $(BIONOMIA_CLAIMS_RB_FILTERED_CSV) $@

$(OCC_SUMMARY_W_PROFILES_FILE): $(VENV_SENTINEL) migrate_profile_rels.py $(BIONOMIA_CLAIMS_RB_FILTERED_CSV) $(BIONOMIA_PROFILES_FILTERED_CSV) $(OCC_CLUSTERED_FILE) $(OCC_SUMMARY_FILE)
	$(PYTHON) migrate_profile_rels.py $(BIONOMIA_CLAIMS_RB_FILTERED_CSV) $(BIONOMIA_PROFILES_FILTERED_CSV) $(OCC_CLUSTERED_FILE) $(OCC_SUMMARY_FILE) $@

clu2profile: $(OCC_SUMMARY_W_PROFILES_FILE)

db: $(DATA_DIR)/geonomia-$(GBIF_DOWNLOAD_COUNTRYCODE).db

# OCC_FILE := $(DOWNLOAD_DIR)/occurrences-$(GBIF_DOWNLOAD_COUNTRYCODE).zip
# CLUSTERED_STAGE1_FILE := $(DOWNLOAD_DIR)/occurrences-$(GBIF_DOWNLOAD_COUNTRYCODE)-clustered-stage1.tsv
# SUMMARY_STAGE1_FILE := $(DOWNLOAD_DIR)/occurrences-$(GBIF_DOWNLOAD_COUNTRYCODE)-clustered-stage1-summary.tsv

#$(OCC_FILE_TSV): $(VENV_SENTINEL) join.py $(OCC_FILE_ZIP) $(OCC_CLUSTERED_FILE)
#	mkdir -p $(DATA_DIR)
#	$(PYTHON) join.py $(OCC_FILE_ZIP) $(OCC_CLUSTERED_FILE) $@
#join: $(OCC_FILE_TSV)

# $(BIONOMIA_CLAIMS_RB_FILTERED_CSV): $(BIONOMIA_CLAIMS_RB_FILTERED_CSV_GZ)
# 	mkdir -p $(DATA_DIR)
# 	gunzip -c $< > $@	

$(DATA_DIR)/rb_rn_yr.tsv: $(VENV_SENTINEL) occclu2reconciliationbackend.py $(OCC_FILE_TSV)
	mkdir -p $(DATA_DIR)
	$(PYTHON) occclu2reconciliationbackend.py $(OCC_FILE_TSV) \
			--source_fields 'recordedby_first_familyname,recordnumber_mainnumber,year' \
			--separator ' ' \
			--id_col 'gbifid' \
			--cluster_id_col 'cluster_stage1_id' \
			--destination_id_col 'gbifid' \
			--destination_field 'reconciliation_backend_key' \
			$@

$(DATA_DIR)/rb_day.tsv: $(VENV_SENTINEL) occclu2reconciliationbackend.py $(OCC_FILE_TSV)
	mkdir -p $(DATA_DIR)
	$(PYTHON) occclu2reconciliationbackend.py $(OCC_FILE_TSV) \
			--source_fields 'recordedby_first_familyname,eventdate' \
			--separator ' ' \
			--id_col 'gbifid' \
			--cluster_id_col 'cluster_stage1_id' \
			--destination_id_col 'cluster_stage1_id' \
			--destination_field 'reconciliation_backend_key' \
			$@

# Make a separate table for GBIF dataset metadata, so we can show meaningful dataset names in the UI, rather than just the dataset keys.
$(DATA_DIR)/dataset_metadata.tsv: $(VENV_SENTINEL) get_dataset_metadata.py $(OCC_FILE_TSV)
	mkdir -p $(DATA_DIR)
	$(PYTHON) get_dataset_metadata.py $(OCC_FILE_TSV) --dataset_col_name datasetkey $@

$(DATA_DIR)/geonomia-$(GBIF_DOWNLOAD_COUNTRYCODE).db: $(VENV_SENTINEL) $(OCC_FILE_TSV) $(OCC_SUMMARY_W_PROFILES_FILE) $(BIONOMIA_CLAIMS_RB_FILTERED_CSV) $(BIONOMIA_PROFILES_FILTERED_CSV) $(DATA_DIR)/rb_rn_yr.tsv $(DATA_DIR)/dataset_metadata.tsv $(OCC_WITH_PROFILES_FILE)
	mkdir -p $(DATA_DIR)
	$(SQLITE_UTILS) create-database $@
	$(SQLITE_UTILS) insert $@ cluster $(OCC_SUMMARY_W_PROFILES_FILE) --tsv --detect-types --pk=cluster_stage1_id
	$(SQLITE_UTILS) insert $@ occ $(OCC_WITH_PROFILES_FILE) --tsv --detect-types
	$(SQLITE_UTILS) transform $@ occ --add-foreign-key cluster_stage1_id cluster cluster_stage1_id
	$(SQLITE_UTILS) enable-fts $@ occ locality recordedBy
	$(SQLITE_UTILS) enable-fts $@ cluster habitat itinerary collecting_areas
	$(SQLITE_UTILS) insert $@ profile $(BIONOMIA_PROFILES_FILTERED_CSV) --tsv --detect-types  --pk=Object
	$(SQLITE_UTILS) transform $@ cluster --add-foreign-key profile_Object profile Object
	$(SQLITE_UTILS) create-index $@ occ cluster_stage1_id
	$(SQLITE_UTILS) insert $@ reconcile_rb_rn_yr $(DATA_DIR)/rb_rn_yr.tsv --tsv --detect-types --pk=gbifid
	$(SQLITE_UTILS) create-index $@ reconcile_rb_rn_yr reconciliation_backend_key
	$(SQLITE_UTILS) insert $@ dataset $(DATA_DIR)/dataset_metadata.tsv --tsv --detect-types --pk=datasetkey
	$(SQLITE_UTILS) transform $@ occ --add-foreign-key datasetkey dataset datasetkey

data/metadata.json: $(VENV_SENTINEL) get_download_metadata.py resources/metadata.json 
		mkdir -p data
		$(PYTHON) get_download_metadata.py --dbname geonomia-$(GBIF_DOWNLOAD_COUNTRYCODE) --download_id ${GBIF_DOWNLOAD_ID} resources/metadata.json $@

dbmetadata: data/metadata.json

all: db dbmetadata

deploy: all
	cp data/metadata.json $(DATA_DIR_SHARED)/metadata.json
	cp data/geonomia-$(GBIF_DOWNLOAD_COUNTRYCODE).db $(DATA_DIR_SHARED)/geonomia-$(GBIF_DOWNLOAD_COUNTRYCODE).db
	cp -r plugins $(DATA_DIR_SHARED)/plugins

run: $(DATA_DIR)/geonomia-$(GBIF_DOWNLOAD_COUNTRYCODE).db data/metadata.json
	$(DATASETTE) $(DATA_DIR)/geonomia-$(GBIF_DOWNLOAD_COUNTRYCODE).db --cors --setting sql_time_limit_ms 12000 --metadata data/metadata.json --plugins-dir plugins

# newline := $(strip )

# SQL_ELIGIBILITY_QUERY := SELECT eventdate_eligible, recordnumber_eligible, recordedby_eligible, CASE WHEN (eventdate_eligible = 'False' AND recordnumber_eligible = 'False' AND recordedby_eligible = 'False') THEN 'n/a' WHEN cluster_stage1_id = -1 THEN 'noise' WHEN cluster_stage1_id >= 0 THEN 'clustered' ELSE 'n/a' END AS 'clustered', count(*) FROM occ GROUP BY eventdate_eligible, recordnumber_eligible, recordedby_eligible, clustered
# SQL_ELIGIBILITY_QUERY := SELECT eventdate_eligible, recordnumber_eligible, recordedby_eligible, count(*) FROM occ GROUP BY eventdate_eligible, recordnumber_eligible, recordedby_eligible
SQL_ELIGIBILITY_QUERY := SELECT eventdate_eligible, recordnumber_eligible, recordedby_eligible, COUNT(*) as count FROM occ GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
# SQL_ELIGIBILITY_QUERY := SELECT cluster_stage1_id, (cluster_stage1_id IS NULL OR cluster_stage1_id = '') AS 'is_null', COUNT(*) as count FROM occ GROUP BY cluster_stage1_id, (cluster_stage1_id IS NOT NULL AND cluster_stage1_id != '') ORDER BY is_null, cluster_stage1_id

query:
	@echo "Eligibility query for geonomia-$(GBIF_DOWNLOAD_COUNTRYCODE).db:"
	@echo "$(SQL_ELIGIBILITY_QUERY)"
	$(SQLITE_UTILS) query --table $(DATA_DIR)/geonomia-$(GBIF_DOWNLOAD_COUNTRYCODE).db "$(SQL_ELIGIBILITY_QUERY)"
	
cleandb:
	rm -rf $(DATA_DIR)/geonomia-$(GBIF_DOWNLOAD_COUNTRYCODE).db

clean:
	rm -rf $(DATA_DIR) 
	
sterilise: clean
	rm -rf $(DOWNLOAD_DIR)

distclean: sterilise
	rm -rf $(VENV_DIR)

boolinspect: $(VENV_SENTINEL) boolinspect.py $(OCC_CLUSTERED_FILE)
	$(PYTHON) boolinspect.py $(OCC_CLUSTERED_FILE)
