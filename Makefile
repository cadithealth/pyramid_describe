test:
	nosetests --verbose

upload:
	python setup.py sdist upload

examples:
	rm -f doc/example.*
	for fmt in html json pdf rst txt wadl xml yaml ; do \
	  echo "creating '$$fmt' example..." ; \
	  pdescribe example.ini --format "$$fmt" > doc/example."$$fmt" ; \
	done
	@echo "creating 'txt' (ascii) example..."
	@pdescribe example.ini --txt --setting format.default.ascii=true \
	  > doc/example.txt.asc

tag:
	@echo "tagging as version `cat VERSION.txt`..."
	git tag -a "v`cat VERSION.txt`" -m "released v`cat VERSION.txt`"
