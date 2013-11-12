PKGNAME = pyramid_describe
include Makefile.python

examples:
	rm -f doc/example.*
	for fmt in html json pdf rst txt wadl xml yaml ; do \
	  echo "creating '$$fmt' example..." ; \
	  pdescribe example.ini --format "$$fmt" > doc/example."$$fmt" ; \
	done
	@echo "creating 'txt' (ascii) example..."
	@pdescribe example.ini --txt --setting format.default.ascii=true \
	  > doc/example.txt.asc
