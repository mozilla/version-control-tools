import bs4
import json
import requests

BUILDAPI_URL = 'https://secure.pub.build.mozilla.org/buildapi/self-serve'


def read_credentials():
    with open('config.json') as f:
        selfserve = json.load(f)['selfserve']
    return (selfserve['user'], selfserve['passwd'])


def make_buildprops(buildurl, testsurl):
    """Make buildprops for given build and tests urls"""
    buildprops = {}
    buildprops['properties'] = json.dumps({})
    buildprops['files'] = json.dumps([buildurl, testsurl])
    return buildprops


def cancel_all(auth, branch, rev):
    """Cancel all jobs for the given revision"""
    try:
        r = requests.delete(BUILDAPI_URL + '/' + branch + '/rev/' + rev,
                            auth=auth)
    except requests.exceptions.ConnectionError:
        return
    return r.status_code, r.text


def post_new_job(auth, branch, buildername, rev, buildprops):
    """Post a test job"""
    try:
        r = requests.post(BUILDAPI_URL + '/' + branch + '/builders/' +
                          buildername + '/' + rev, auth=auth, data=buildprops)
    except requests.exceptions.ConnectionError:
        return
    return r.status_code, r.text


def rebuild_job(auth, branch, build_id, count=1):
    """Rebuild a job"""
    data = {'build_id': build_id, 'count': count}
    try:
        r = requests.post(BUILDAPI_URL + '/' + branch + '/build', auth=auth,
                          data=data)
    except requests.exceptions.ConnectionError:
        return
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.text)
        # extract job id, not initially available in json blob
        title = soup.find('title')
        if title:
            return title.text.split()[1]


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
