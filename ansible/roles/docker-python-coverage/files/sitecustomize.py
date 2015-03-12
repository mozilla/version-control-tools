import os

if os.path.exists('/collect-coverage'):
    import uuid
    import coverage

    covpath = '/coverage/coverage.%s' % uuid.uuid1()
    cov = coverage.coverage(data_file=covpath, auto_data=True)
    cov._warn_no_data = False
    cov._warn_unimported_source = False
    cov.start()
