NC2XML = ./src/nc2xml.py
XMLLINT = xmllint

NC_FILE = data/clm_params_ed.c161103.nc
OUTPUT_FILE = junk.xml
SCHEMA = src/parameters.xsd

test : FORCE
	$(NC2XML) --backtrace --netcdf-file $(NC_FILE) --output-file $(OUTPUT_FILE)
	$(XMLLINT) --noout --schema $(SCHEMA) $(OUTPUT_FILE)

clean : FORCE
	rm *~ src/*~ junk.*

FORCE :
