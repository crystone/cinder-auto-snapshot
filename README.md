# WARNING! THIS IS NOT MAINTAINED OR USED ANYMORE AND HAS SEVERAL FLAWS AND LEAVES ORPHANED SNAPSHOTS SINCE THEY ARE CREATED ON THE ADMIN ACCOUNT AND NOT CLEANED WHEN A VOLUME IS DELETED

# cinder-auto-snapshot
Python based script that creates snapshots and deletes old snapshots to perform tasks similar to a backup software.
Tested on OpenStack Liberty

Any improvements are welcome, feel free to create a pull request.

## Status
[![Build Status](https://travis-ci.org/tobias-urdin/cinder-auto-snapshot.svg?branch=master)](https://travis-ci.org/tobias-urdin/cinder-auto-snapshot)

## Requirements
See requirements.txt for pip requirements, use 'pip install -r requirements.txt' to install requirements using pip or use your package manager.

If you don't have pip, use 'easy_install pip' to install pip.

* python 2.6 or 2.7
* python-cinderclient

## Installation
* Make sure /etc/cinder and /var/log/cinder folders exists.
* Copy sample config file to /etc/cinder
* Copy the cinder-auto-snapshot.py file to where you wanna have it, we recommend something like /usr/local/sbin.

You can now run the script manually or add a cron job to run it, check the log file for any errors.

## Example cron job
/etc/cron.d/cinder-auto-snapshot
```
# Performs cinder snapshots using cinder-auto-snapshot
0 1 * * * root if [ -x /usr/local/sbin/cinder-auto-snapshot ] ; then /usr/local/sbin/cinder-auto-snapshot >/dev/null 2>&1; fi
```

## License
cinder-auto-snapshot
Copyright (C) 2015 Tobias Urdin

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
