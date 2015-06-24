import bs4
import config
import json
import requests

BUILDAPI_URL = 'https://secure.pub.build.mozilla.org/buildapi/self-serve'


def read_credentials():
    return config.get('selfserve')['user'], config.get('selfserve')['passwd']


def job_status(auth, job_id):
    """Get job status for provided job_id"""
    try:
        r = requests.get(BUILDAPI_URL + '/jobs/' + job_id, auth=auth)
    except requests.exceptions.ConnectionError:
        return
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.text)
        pre = soup.find('pre')
        if pre:
            return json.loads(pre.text)


def job_is_done(auth, branch, rev):
    """Determine whether a job is done"""
    try:
        r = requests.get(BUILDAPI_URL + '/' + branch + '/rev/' + rev +
                         '/is_done', auth=auth)
    except requests.exceptions.ConnectionError:
        return
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.text)
        return json.loads(soup.text)
    elif r.status_code == 404:
        soup = bs4.BeautifulSoup(r.text)
        pre = soup.find('pre')
        if pre:
            return json.loads(pre.text)


def build_info(auth, branch, build_id):
    try:
        r = requests.get(BUILDAPI_URL + '/' + branch + '/build/' + build_id,
                         auth=auth)
    except requests.exceptions.ConnectionError:
        return
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.text)
        return json.loads(soup.text)


def jobs_for_revision(auth, branch, rev):
    """Get job status for provided request_id"""
    try:
        r = requests.get(BUILDAPI_URL + '/' + branch + '/rev/' + rev,
                         auth=auth)
    except requests.exceptions.ConnectionError:
        return
    soup = bs4.BeautifulSoup(r.text)
    pending = []
    running = []
    builds = []
    for table in soup.find_all('table'):
        t_id = table.attrs.get('id', '')
        for i in table.find_all('input'):
            if t_id == 'pending' and i.attrs.get('name', '') == 'request_id':
                pending.append(i.attrs['value'])
            elif t_id == 'running' and i.attrs.get('name', '') == 'build_id':
                running.append(i.attrs['value'])
            elif t_id == 'builds' and i.attrs.get('name', '') == 'build_id':
                builds.append(i.attrs['value'])
    return pending, running, builds
