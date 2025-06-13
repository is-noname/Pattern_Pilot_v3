# docs/Makefile
.PHONY: help clean html autodoc

SPHINXOPTS    ?=
SPHINXBUILD  ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	@$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	rm -rf source/api/generated/

html:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

autodoc:
	sphinx-autogen -o source/api/generated source/api/modules.rst

# Trading-spezifisches Target
trading-docs: clean autodoc html
	@echo "Trading Terminal Documentation built successfully"