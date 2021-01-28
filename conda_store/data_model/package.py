import logging
import datetime

from conda_store.conda import download_repodata

logger = logging.getLogger(__name__)


def update_conda_channels(dbm, channels=None, update_interval=60*60):
    channels = channels or {'https://repo.anaconda.com/pkgs/main', 'https://conda.anaconda.org/conda-forge'}

    with dbm.transaction() as cursor:
        cursor.execute('SELECT last_package_update FROM conda_store WHERE id = 1')
        last_package_update = cursor.fetchone()['last_package_update']

        # don't update packages if last update was less than update_interval seconds ago
        if last_package_update is not None and (last_package_update + datetime.timedelta(seconds=update_interval) > datetime.datetime.now()):
            logger.info(f'packages were updated in the last seconds={update_interval}')
            return

        for channel in channels:
            add_channel_packages(dbm, channel)

        cursor.execute('UPDATE conda_store SET last_package_update = ?', (datetime.datetime.now(),))


def add_channel_packages(dbm, channel):
    repodata = download_repodata(channel)

    with dbm.transaction() as cursor:
        for architecture in repodata:
            packages = list(repodata[architecture]['packages'].values())
            for package in packages:
                cursor.execute('''
                  INSERT OR IGNORE INTO conda_package
                  (build, build_number, constrains, depends, license, license_family, md5, sha256, name, size, subdir, timestamp, version, channel)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    package['build'],
                    package['build_number'],
                    package.get('constrains'),
                    package['depends'],
                    package.get('license'),
                    package.get('license_family'),
                    package['md5'],
                    package['sha256'],
                    package['name'],
                    package['size'],
                    package.get('subdir'),
                    package.get('timestamp'),
                    package['version'],
                    channel,
                ))


def link_packages_to_build(dbm, build_id, conda_packages):
    with dbm.transaction() as cursor:
        cursor.executemany('''
          INSERT INTO build_package
          SELECT
            ? AS build_id,
            conda_package.id AS conda_package_id
          FROM conda_package
          WHERE channel = ?
            AND subdir = ?
            AND name = ?
            AND version = ?
            AND build = ?
            AND build_number = ?
        ''', [(build_id, _['base_url'], _['platform'], _['name'], _['version'], _['build_string'], _['build_number']) for _ in conda_packages])
