class reviewboard {
  include apache
  include mysql::server

  $files = '/version-control-tools/testing/puppet/files'

  user { 'reviewboard':
    gid      => 'reviewboard',
    groups   => ['reviewboard'],
    uid      => 1003,
    shell    => '/bin/bash',
    password => 'reviewboard',
  }

  group { 'reviewboard':
    gid => 501,
  }

  file { '/home/reviewboard':
    ensure  => directory,
    owner   => 'reviewboard',
    group   => 'reviewboard',
    require => User['reviewboard'],
  }

  class { 'python':
    dev        => true,
    pip        => true,
    virtualenv => true,
  }

  package { 'libmysqlclient-dev':
    ensure => present,
  }

  python::virtualenv { '/home/reviewboard/venv':
    require      => Package['libmysqlclient-dev'],
    ensure       => present,
    version      => 'system',
    requirements => '/version-control-tools/test-requirements.txt',
    owner        => 'reviewboard',
    group        => 'reviewboard',
    cwd          => '/home/reviewboard',
  }

  exec { 'install_reviewboard':
    require => Python::Virtualenv['/home/reviewboard/venv'],
    command => '/home/reviewboard/venv/bin/easy_install ReviewBoard==2.0.2',
    user    => 'reviewboard',
    cwd     => '/home/reviewboard',
  }

  file { '/home/reviewboard/venv/lib/python2.7/site-packages/mozreview.pth':
    require => Python::Virtualenv['/home/reviewboard/venv'],
    content => '/version-control-tools/pylib/mozreview',
    owner   => 'reviewboard',
    group   => 'reviewboard',
  } -> Exec['rbsetup']

  file { '/home/reviewboard/venv/lib/python2.7/site-packages/rbmozui.pth':
    require => Python::Virtualenv['/home/reviewboard/venv'],
    content => '/version-control-tools/pylib/rbmozui',
    owner   => 'reviewboard',
    group   => 'reviewboard',
  } -> Exec['rbsetup']

  file { '/home/reviewboard/venv/lib/python2.7/site-packages/rbbz.pth':
    require => Python::Virtualenv['/home/reviewboard/venv'],
    content => '/version-control-tools/pylib/rbbz',
    owner   => 'reviewboard',
    group   => 'reviewboard',
  } -> Exec['rbsetup']

  mysql_database { 'reviewboard':
    ensure  => 'present',
    charset => 'utf8',
  } -> mysql_user { 'reviewboard@localhost':
    ensure        => 'present',
    # reviewboard
    password_hash => '*E9DFA5B14F817324A5F00B8A70FC6908174719ED',
  } -> mysql_grant { 'reviewboard@localhost/reviewboard.*':
    ensure     => 'present',
    options    => ['GRANT'],
    privileges => ['ALL'],
    table      => 'reviewboard.*',
    user       => 'reviewboard@localhost',
  } -> exec { 'rbsetup':
    command     => "/home/reviewboard/venv/bin/python $files/rbserverconfigure.py /home/reviewboard/site",
    user        => 'reviewboard',
  } ~> Service['httpd']

  class { '::apache::mod::wsgi': }

  ::apache::vhost { 'reviewboard':
    require       => Exec['rbsetup'],
    port          => 8001,
    docroot       => '/home/reviewboard/site/htdocs',
    docroot_owner => 'reviewboard',
    docroot_group => 'reviewboard',

    directories => [
      {
        path           => '/home/reviewboard/site/htdocs',
        options        => ['-Indexes', '+FollowSymLinks'],
        allow_override => ['All'],
      },
      {
        path     => '/media/uploaded',
        provider => 'location',
        options  => ['None'],
        handler  => 'None',
      },
    ],

    aliases => [
      {
        alias => '/media',
        path  => '/home/reviewboard/site/htdocs/media',
      },
      {
        alias => '/static',
        path  => '/home/reviewboard/site/htdocs/static',
      },
      {
        alias => '/errordocs',
        path  => '/home/reviewboard/site/htdocs/errordocs',
      },
      {
        alias => '/favicon.ico',
        path  => '/home/reviewboard/site/htdocs/static/rb/images/favicon.png',
      },
    ],

    error_documents  => [
      { 'error_code' => '500', 'document' => '/errordocs/500.html' },
    ],

    wsgi_script_aliases => {
      '/' => '/home/reviewboard/site/htdocs/reviewboard.wsgi/',
    },

    additional_includes => [
      "$files/reviewboard.vhost.conf",
    ],
  }
}
