test:
	nosetests --verbose

upload:
	python setup.py sdist upload

examples:
	for fmt in html json rst txt wadl xml yaml ; do \
	  echo "creating '$$fmt' example..." ; \
	  pdescribe example.ini --format "$$fmt" > doc/example."$$fmt" ; \
	done
	@echo "creating 'txt' (ascii) example..."
	@pdescribe example.ini --txt --setting format.default.ascii=true \
	  > doc/example.txt.asc
