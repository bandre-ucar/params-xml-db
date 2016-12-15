NCGEN = ncgen
NCDUMP = ncdump

CDL = \
	clm_params_ed.c161103.cdl

NC = $(CDL:%.cdl=%.nc)


#
# Generic rule to generate files
#
%.nc : %.cdl
	$(NCGEN) -o $@ $<

all : $(NC)

