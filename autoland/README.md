autoland
========

Installation
------------

Install required ubuntu packages:

    sudo apt-get update
    sudo apt-get install git pip python-dev postgresql libqu-dev libldap2-dev libsasl2-dev

Create a virtualenv:

    sudo pip install virtualenv
    virtualenv venv
    . venv/bin/activate

Install python libs

    pip install -r requirements.txt

Create the autoland database:

    cd sql
    sudo -u postgres ./createdb.sh
