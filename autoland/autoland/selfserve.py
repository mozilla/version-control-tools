import bs4 
import json
import requests

BUILDAPI_URL = 'https://secure.pub.build.mozilla.org/buildapi/self-serve'

def read_credentials():
    user, passwd = open('credentials.txt').read().strip().split(',')
    return (user, passwd)

def make_buildprops(buildurl, testsurl):
    """Make buildprops for given build and tests urls""" 
    buildprops = {}
    buildprops['properties'] = json.dumps({})
    buildprops['files'] = json.dumps([buildurl, testsurl])
    return buildprops

def post_new_job(auth, branch, buildername, rev, buildprops):
    """Post a test job"""
    r = requests.post(BUILDAPI_URL + '/' + branch + '/builders/' + buildername + '/' + rev, auth=auth, data=buildprops)
    return r.status_code, r.text

def rebuild_job(auth, branch, build_id, count=1):
    """Rebuild a job"""
    data = {'build_id': build_id, 'count': count}
    r = requests.post(BUILDAPI_URL + '/' + branch + '/build', auth=auth, data=data)
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.text)
        # extract job id, not initially available in json blob
        title = soup.find('title')
        if title:
            return title.text.split()[1] 

def job_status(auth, job_id):
    """Get job status for provided job_id"""
    r = requests.get(BUILDAPI_URL + '/jobs/' + job_id, auth=auth)
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.text)
        pre = soup.find('pre')
        if pre:
            return json.loads(pre.text)

def job_is_done(auth, branch, rev):
    """Determine whether a job is done"""
    r = requests.get(BUILDAPI_URL + '/' + branch + '/rev/' + rev + '/is_done', auth=auth)
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.text)
        return json.loads(soup.text)

def build_info(auth, branch, build_id):
    r = requests.get(BUILDAPI_URL + '/' + branch + '/build/' + build_id, auth=auth)
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.text)
        return json.loads(soup.text)

def jobs_for_revision(auth, branch, rev):
    """Get job status for provided request_id"""
    r = requests.get(BUILDAPI_URL + '/' + branch + '/rev/' + rev, auth=auth)
    soup = bs4.BeautifulSoup(r.text)
    pending = []
    running = []
    builds = []
    for table in soup.find_all('table'):
        table_id = table.attrs.get('id', '')
        for i in table.find_all('input'):
            if table_id == 'pending' and i.attrs.get('name', '') == 'request_id':
                pending.append(i.attrs['value'])
            elif table_id == 'running' and i.attrs.get('name', '') == 'build_id':
                running.append(i.attrs['value'])
            elif table_id == 'builds' and i.attrs.get('name', '') == 'build_id':
                builds.append(i.attrs['value'])
    return pending, running, builds 
