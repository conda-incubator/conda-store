from conda_store.conda import download_repodata


def add_channel_packages(dbm, channel):
    repodata = download_repodata(channel)

    with dbm.transaction() as cursor:
        for architecture in repodata:
            packages = list(repodata[architecture]['packages'].values())
            for package in packages:
                cursor.execute('''
                  INSERT OR IGNORE INTO package
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
