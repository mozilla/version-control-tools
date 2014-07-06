class bugzilla {
  $files = '/version-control-tools/testing/puppet/files'

  $packages = [
    'build-essential',
    'g++',
    'graphviz',
    'libdaemon-generic-perl',
    'libgd-dev',
    'libssl-dev',
    # Installing PerlMagick from CPAN gives a compiler error.
    'perlmagick',
    'pkg-config',
    'unzip',
  ]

  package { $packages:
    ensure       => installed,
  }

  user { 'bugzilla':
    gid      => 'bugzilla',
    groups   => ['bugzilla'],
    uid      => 1002,
    shell    => '/bin/bash',
    password => 'bugzilla',
  }

  group { 'bugzilla':
    gid => 500,
  }

  file { '/home/bugzilla':
    ensure  => directory,
    owner   => 'bugzilla',
    group   => 'bugzilla',
    require => User['bugzilla'],
  }

  vcsrepo { 'bugzilla':
    path     => '/home/bugzilla/bugzilla',
    source   => 'https://git.mozilla.org/webtools/bmo/bugzilla.git',
    provider => git,
    owner    => bugzilla,
    group    => bugzilla,
    ensure   => latest,
    revision => 'production',
    require  => File['/home/bugzilla'],
  }

  file { '/home/bugzilla/bugzilla':
    mode    => 0755,
    owner   => bugzilla,
    group   => bugzilla,
    require => Vcsrepo["bugzilla"],
  }

# Changing this will cause the log file to be deleted. Due to
# Exec['fix_innodb']. You have been warned.
  $innodb_log_file_megabytes = 512
  $innodb_log_file_bytes = $innodb_log_file_megabytes * 1024 * 1024

  class { '::mysql::server':
    # BMO uses 5.6. Ubuntu 14.04 ships with 5.5 by default.
    package_name   => 'mysql-server-5.6',
    purge_conf_dir => true,
    root_password  => 'root',
    override_options         => {
      'mysql'                => {
        'max_allowed_packet' => '1G',
      },
      'mysqld'                    => {
        'default_storage_engine'  => 'InnoDB',
        'key_buffer_size'         => '32M',
        'max_allowed_packet'      => '1G',
        'innodb'                  => 'FORCE',
        'character-set-server'    => 'utf8mb4',
        'collation-server'        => 'utf8mb4_general_ci',

        'tmp_table_size'         => '32M',
        'max_heap_table_size'    => '32M',
        'query_cache_type'       => '0',
        'query_cache_size'       => '0',
        'max_connections'        => '500',
        'thread_cache_size'      => '50',
        'table_definition_cache' => '1024',
        'table_open_cache'       => '2048',

        'innodb_flush_method'            => 'O_DIRECT',
        # 0 is optimized for SSDs.
        'innodb_flush_neighbors'         => '0',
        'innodb_log_files_in_group'      => '2',
        'innodb_log_file_size'           => "${innodb_log_file_megabytes}M",
        # This is a bit large to optimize for bulk inserts.
        'innodb_log_buffer_size'         => '64M',
        'innodb_flush_log_at_trx_commit' => '2',
        'innodb_file_per_table'          => '1',
        # Decrease this if you don't run the VM with 4 GB of memory.
        'innodb_buffer_pool_size'       => '2G',
        'innodb_write_io_threads'       => '8',
        'innodb_read_io_threads'        => '8',
        'innodb_change_buffer_max_size' => '75',

        'log_error' => '/var/lib/mysql/mysql-error.log',
      },
    },
  }

  mysql_database { 'bugs':
    ensure  => 'present',
    charset => 'utf8',
  } -> mysql_user { 'bugs@localhost':
    ensure => 'present',
    # bugs
    password_hash => '*F6143BCA58806D14CD1C97998C6792405D8AE8AE',
  } -> mysql_grant { 'bugs@localhost/*.*':
    ensure     => 'present',
    options    => ['GRANT'],
    privileges => 'ALL',
    table      => '*.*',
    user       => 'bugs@localhost',
  }

  # We adjust the default innodb log file sizes. This causes MySQL to
  # throw a fit about mismatched size because the log files created during
  # package install and subsequent initial run are a different size from
  # the config. We forcefully remove the log file after log file size
  # change.
  exec { 'fix_innodb':
    command   => "/sbin/stop mysql; /bin/rm /var/lib/mysql/ib_logfile0 /var/lib/mysql/ib_logfile1",
    onlyif    => "/usr/bin/test -e /var/lib/mysql/ib_logfile0 -a \$(/usr/bin/du -b /var/lib/mysql/ib_logfile0 | /usr/bin/awk '{ print \$1 }') -ne ${innodb_log_file_bytes}}",
  }

  Class['mysql::server::config'] ~> Exec['fix_innodb'] ~> Class['mysql::server::service']

  # Bugzilla dump file to load. This is optional.
  # Dumps can be obtained from https://people.mozilla.org/~mhoye/bugzilla/.
  $bmo_dump_file = 'Mozilla-Bugzilla-Public-*.sql.gz'

  exec { 'load_bmo':
    onlyif  => [
      "/usr/bin/test -f $files/${bmo_dump_file}",
      "/usr/bin/test ! -f /home/bugzilla/bmo_loaded",
    ],
    user    => 'bugzilla',
    command => "/bin/zcat $files/${bmo_dump_file} | $files/fastimport.py | /usr/bin/mysql -ubugs -pbugs bugs && /usr/bin/touch /home/bugzilla/bmo_loaded",
    timeout => 14400,
  }

  Class['mysql::server'] ~> Exec['load_bmo']

  exec { 'reset_git':
    require => Vcsrepo['bugzilla'],
    command => '/usr/bin/git reset --hard HEAD && /usr/bin/git clean -f',
    user    => 'bugzilla',
    cwd     => '/home/bugzilla/bugzilla',
  }

  # ElasticSearch isn't available on CPAN. Hack around failure installing
  # it.
  exec { 'patch_es':
    require => Exec['reset_git'],
    before  => Exec['bzmodules'],
    command => "/usr/bin/patch -p1 < $files/elasticsearch.patch",
    user    => 'bugzilla',
    cwd     => '/home/bugzilla/bugzilla',
  }

  exec { 'bzmodules':
    require => [Exec['patch_es'], Package[$packages], Class[::mysql::server]],
    command => '/home/bugzilla/bugzilla/install-module.pl --all',
    user    => 'bugzilla',
    cwd     => '/home/bugzilla/bugzilla',
    timeout => 1800,
  }

  # Linux::Pid is a dependency for Apache::SizeLimit. For whatever reason
  # it isn't detected by CPAN.
  # XMLRPC::Transport::HTTP is needed by xmlrpc.cgi. For whatever reason
  # the dependency isn't installed.
  exec { 'pm_extra':
    require => Vcsrepo['bugzilla'],
    command => '/home/bugzilla/bugzilla/install-module.pl Linux::Pid XMLRPC::Transport::HTTP',
    user    => 'bugzilla',
    cwd     => '/home/bugzilla/bugzilla',
  }

  # Bug 769829. Foreign key issue with component watch schema updating.
  exec { 'patch_db':
    before  => Exec['bzchecksetup'],
    require => Exec['reset_git'],
    command => "/usr/bin/patch -p1 < $files/fkpatch.patch",
    user    => 'bugzilla',
    cwd     => '/home/bugzilla/bugzilla',
  }

  # Bug 1034678. Error creating default product.
  # This is only relevant is we don't do a BMO load. But it's harmless of
  # we do.
  exec { 'patch_defaultproduct':
    before   => Exec['bzchecksetup'],
    require  => Exec['reset_git'],
    command  => "/usr/bin/patch -p1 < $files/nodefaultproduct.patch",
    user     => 'bugzilla',
    cwd      => '/home/bugzilla/bugzilla',
  }

  # The .htaccess isn't compatible with Apache 2.4. We fix that.
  exec { 'patch_htaccess':
    require => Exec['reset_git'],
    before  => Service['httpd'],
    command => "/usr/bin/patch -p1 < $files/apache24.patch",
    user    => 'bugzilla',
    cwd     => '/home/bugzilla/bugzilla',
  }

  # checksetup.pl appears to not always refresh data/params if the
  # answers have been updated. Force it by removing output.
  file { '/home/bugzilla/bugzilla/data':
    ensure  => absent,
    recurse => true,
    force   => true,
  }

  exec { 'bzchecksetup':
    require  => [Exec['bzmodules'], Exec['load_bmo'], File['/home/bugzilla/bugzilla/data']],
    command  => "/home/bugzilla/bugzilla/checksetup.pl $files/checksetup_answers.txt",
    user     => 'bugzilla',
    cwd      => '/home/bugzilla/bugzilla',
  }

  # Restore pristine repo state (undo local patch hacks).
  exec { 'unpatch_bugzilla':
    require => Exec['bzchecksetup'],
    command => '/usr/bin/git checkout -- Bugzilla/DB.pm Bugzilla/Install/Requirements.pm checksetup.pl',
    user    => 'bugzilla',
    cwd     => '/home/bugzilla/bugzilla',
  }

  file { '/etc/apache2/conf.d/50perlswitches.conf':
    source => "$files/apache_perlswitches.conf",
    owner  => 'root',
    group  => 'root',
    notify => Service['httpd'],
  }

  class { 'apache':
    default_vhost => false,
    group         => 'bugzilla',
    manage_group  => false,
    mpm_module    => 'prefork',
  }

  class { 'apache::mod::perl': }
  class { 'apache::mod::rewrite': }

  apache::vhost { 'bugzilla':
    port        => '80',
    docroot     => '/home/bugzilla/bugzilla',
    directories => [
      {
        path           => '/home/bugzilla/bugzilla',
        addhandlers    => [{ handler => 'cgi-script', extensions => ['.cgi'] }],
        directoryindex => 'index.cgi',
        allow_override => ['All'],
        options        => ['Indexes', 'FollowSymLinks', 'ExecCGI'],
      },
    ],
    additional_includes => "$files/apache_extra.conf",
    require             => Exec['pm_extra'],
  }
}
