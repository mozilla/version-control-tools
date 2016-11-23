.PHONY = docker mountebank rabbitmq test clean

PYTHON = python2.7

default: docker venv

docker: mountebank rabbitmq

mountebank:
	docker build -t mountebank docker-mountebank/

rabbitmq:
	docker pull rabbitmq:3-management

venv:
	virtualenv --no-site-packages --python=$(PYTHON) venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -e .

test:
	venv/bin/pytest tests

clean:
	rm -r venv/