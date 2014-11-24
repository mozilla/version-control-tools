import kombu 
import os
import pytz
import platform
import sys

from datetime import datetime

MOZDEF_PORT = 5671


def read_credentials():
    user, passwd, server = open('credentials/mozdef.txt').read().strip().split(',')
    return (user, passwd, server)


def post(auth, data):
    conn_string = 'amqp://{0}:{1}@{2}:{3}/autoland'.format(auth[0], auth[1],
                                                           auth[2], MOZDEF_PORT)
    conn = kombu.Connection(conn_string, ssl=True)
    exchange = kombu.Exchange('eventtask', type='direct', durable=True)
    exchange(conn).declare()
    producer = conn.Producer(serializer='json')
    publisher = conn.ensure(producer, producer.publish, max_retries=10)
    publisher(data, exchange=exchange, routing_key='eventtask')


def post_ldap_group_check(auth, user, group, result):
    now = pytz.timezone('UTC').localize(datetime.utcnow()).isoformat()

    data = {
        'utctimestamp': now,
        'hostname': platform.node(),
        'processname': sys.argv[0],
        'processid': os.getpid(),
        'severity': 'INFO',
        'summary': 'LDAP autoland group membership check',
        'category': 'event',
        'source': '',
        'tags': [
            'Autoland',
            'Authentication'
        ],
        'details': {
            'user': user,
            'group': group, 
            'in_group': result
        }
    }
    post(auth, data)
