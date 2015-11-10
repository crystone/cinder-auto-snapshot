#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# cinder-auto-snapshot
# Copyright (C) 2015 Crystone Sverige AB

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# NOTE:
# It's important that we always return an exit code of above 0 if not
# successful since we want to be able to use this in a shell script
# and check the return code.
# 0 = OK
# 1 = ERROR
# 2 = WARNING

import sys
import os
import logging
import time
import datetime
import ConfigParser


# Provide some 'project' info.
PROJECT_NAME = 'cinder-auto-snapshot'
VERSION = '1.0'

# Config and log file to use.
LOGFILE = '/var/log/cinder/cinder-auto-snapshot.log'
CONFIGFILE = '/etc/cinder/cinder-auto-snapshot.cfg'

# Setup the logging
logger = logging.getLogger(__name__)

loggerFile = logging.FileHandler(LOGFILE)
loggerFormat = logging.Formatter('%(asctime)s cinder-auto-snapshot %(levelname)s %(message)s')

loggerFile.setFormatter(loggerFormat)
logger.addHandler(loggerFile)

logger.setLevel(logging.INFO)

# Load config.
config = ConfigParser.RawConfigParser()

try:
    config.read(CONFIGFILE)
except Exception, e:
    logger.error('Failed to read config file %s: %s' % (READ_CONFIG_FILE, e))
    sys.exit(1)

# Grab some config values.
LOGLEVEL = logging.INFO

if config.getboolean('cinder-auto-snapshot', 'debug'):
    LOGLEVEL = logging.DEBUG

logger.setLevel(LOGLEVEL)
logger.debug('Debug mode is enabled')

try:
    RETENTION = config.getint('cinder-auto-snapshot', 'retention')
except Exception, e:
    logger.error('Failed to get retention from config in section cinder-auto-snapshot: %s' % (e))
    sys.exit(1)

# Grab credentials from config.
credentials = {}

try:
    credentials['auth_url'] = config.get('keystone', 'auth_url')
    credentials['username'] = config.get('keystone', 'username')
    credentials['api_key'] = config.get('keystone', 'password')
    credentials['project_id'] = config.get('keystone', 'project_name')
    credentials['service_type'] = 'volumev2'
except Exception, e:
    logger.error('Failed to grab keystone config: %s' % (e))
    sys.exit(1)

# Import the cinder client if not found catch exception, log it and then exit.
# We must do it here because we want to be able to log it.
try:
    from cinderclient.v2 import client
except ImportError:
    logger.error('You must have python-cinderclient installed to use this, install it using pip or with your package manager.')
    sys.exit(1)

# Check if snapshot with name exists
def check_if_snapshot_exists(cinder, name):
    # Check that the cinder client is valid
    if cinder is None:
        return None

    # Check that the snapshot name is valid
    if name is None:
        return None

    # Options to use when searching for the snapshot
    opts = {
        'all_tenants': 1,
        'name': name
    }

    # Get all snapshots with the above options.
    try:
        existing_snapshots = cinder.volume_snapshots.list(search_opts=opts)
    except Exception, e:
        logger.error('Exception %s when checking for existing snapshots with name %s' % (e, name))
        return False

    # Check that the result is valid.
    if existing_snapshots is None:
        return False

    num_matches = len(existing_snapshots)

    if num_matches > 0:
        return True

    return False

# Get all valid snapshots for a volume
def get_valid_snapshots_for_volume(cinder, volume_id):
    # Check that the cinder client is valid
    if cinder is None:
        return None

    # Check that the volume id is valid
    if volume_id is None:
        return None

    # Options to use when retreiving all volumes.
    # We want to retrieve all snapshots for a volume.
    opts = {
        'all_tenants': 1,
        'volume_id': volume_id
    }

    # Get all snapshots for the volume and catch any exceptions
    # that might occur.
    try:
        snapshots = cinder.volume_snapshots.list(search_opts=opts)
    except Exception, e:
        logger.error('Exception %s when retrieving snapshots for volume %s' % (e, volume_id))
        return None

    # Check that snapshots is valid.
    if snapshots is None:
        return None

    # List to store all valid snapshots which we
    # return at the end.
    data = []

    # Loop through all snapshots found.
    for snapshot in snapshots:
        # Make sure the snapshot name is set.
        if snapshot.name is None:
            continue

        # Save the snapshot name in a string.
        name = str(snapshot.name)

        # Check if the snapshot name starts with our keyword.
        # We don't want to get peoples private snapshots so we
        # use this as a marker.
        if name.startswith('auto-snapshot-'):
            # Append Snapshot object to list.
            data.append(snapshot)

    # Return all our valid snapshots.
    return data

# Main entrypoint
if __name__ == '__main__':
    logger.info('Starting %s version %s' % (PROJECT_NAME, VERSION))

    if credentials is None:
        logger.error('Credentials is None which is invalid.')
        sys.exit(1)

    # Create our python-cinderclient client
    try:
        cinder = client.Client(**credentials)
    except Exception, e:
        logger.error('Exception %s when creating cinder context' % e)
        sys.exit(1)

    # Check so that the cinder context is valid
    if cinder is None:
        logger.error('Error cinder context is None')
        sys.exit(1)

    # Check the current date and time which we use for the
    # name of the backup later on.
    #date = time.strftime("%Y%m%d_%H_%M_%S")
    date = time.strftime("%Y%m%d")
    now = datetime.datetime.now()

    # Options to get volumes and snapshots for all tenants
    # and not only for the project that authenticates.
    # This requires that the user that authenticates has
    # admin privileges.
    opts = {
        'all_tenants': 1
    }

    # Get all volumes for all tenants.
    try:
        volumes = cinder.volumes.list(search_opts=opts)
    except Exception, e:
        logger.error('Exception %s when retrieving volumes' % e)
        sys.exit(1)

    # Check so that our volumes data is not None.
    if volumes is None:
        logger.error('Volumes data is None')
        sys.exit(1)

    # Loop through all volumes and create a daily snapshot.
    # The name is very important since we later on when we
    # loop through the snapshots looks for the auto-snapshot
    # keyword so we don't delete peoples private snapshots.
    for volume in volumes:
        # Note: We skip the volume 'dont-delete-me-im-monitored-by-nagios'
        # because it's a simple test volume that makes the volumes count
        # above 0 so that our nagios can verify that the Cinder API is
        # working properly.
        if volume.name == 'dont-delete-me-im-monitored-by-nagios':
            continue

        # Set name of snapshot to something that we easily
        # can match later on when deleting old snapshots.
        # See the get_valid_snapshots_for_volume function.
        snapshot_name = 'auto-snapshot-%s-%s' % (volume.id, date)

        # Check if a snapshot with that name already exists.
        if check_if_snapshot_exists(cinder, snapshot_name) == True:
            logger.info('Snapshot with name %s already exists for volume %s not creating another snapshot' % (snapshot_name, volume.id))
            continue

        # Set a simple description which we can use on the snapshot.
        snapshot_desc = 'Automatic snapshot created by cinder-auto-snapshot'

        logger.info('Creating snapshot of %s named %s' % (volume.id, snapshot_name))

        # Create the snapshot and catch any exceptions that might occur.
        try:
            new_snapshot = cinder.volume_snapshots.create(volume_id=volume.id, force=True, name=snapshot_name, description=snapshot_desc)
        except Exception, e:
            logger.error('Exception %s when creating snapshot of volume %s' % (e, volume.id))
            continue

        # Check that our new snapshot is not None.
        if new_snapshot is None:
            logger.error('New snapshot for volume %s is invalid' % (volume.id))
            continue

        logger.info('Successfully created new snapshot %s of volume %s' % (new_snapshot.id, volume.id))

        # Get all valid snapshots for volume and catch any exception that might occur.
        try:
            snapshots = get_valid_snapshots_for_volume(cinder, volume.id)
        except Exception, e:
            logger.error('Exceptions %s when calling get_valid_snapshots_for_volume for volume %s' % (e, volume.id))
            continue

        # Check that our snapshots data is not None.
        if snapshots is None:
            logger.error('Snapshots for volume %s is None' % (volume.id))
            continue

        # Get amount of valid snapshots found.
        valid_snapshots_count = len(snapshots)

        # Check that we have atleast the same amount of valid snapshots
        # as the amount of retention days otherwise we continue and dont cleanup.
        if valid_snapshots_count <= int(RETENTION):
            logger.warning('Volume %s has %s valid snapshots which is below the retention of %s, skipping snapshot cleanup.' % (volume.id, valid_snapshots_count, RETENTION))
            continue

        # Loop through all valids snapshots.
        for snapshot in snapshots:
            logger.debug('Found snapshot %s %s' % (snapshot.id, snapshot.name))

            # Parse the created_at date for the snapshot.
            created = datetime.datetime.strptime(snapshot.created_at, '%Y-%m-%dT%H:%M:%S.%f')

            # Calculate delta between current date and creation date to determine
            # how many days since it was created.
            delta = now - created

            # Check if the snapshot is older than the configured days of retention.
            # If it's older we delete it, otherwise we just ignore it.
            if int(delta.days) > int(RETENTION):
                logger.info('Snapshot %s of volume %s will be deleted because it is %s days old which exceeds the retention period of %s days' % (snapshot.id, snapshot.volume_id, delta.days, RETENTION))

                # Save snapshot id
                snapshot_id = snapshot.id

                # Delete the snapshot.
                try:
                    cinder.volume_snapshots.delete(snapshot)
                except Exception, e:
                    logger.error('Failed to delete snapshot %s of volume' % (snapshot.id, volume.id))
                    continue

                logger.info('Snapshot %s was successfully deleted' % (snapshot_id))
            else:
                # Don't delete the snapshot, it's not old enough.
                logger.info('Snapshot %s of volume %s will not be deleted, its only %s days old which is below the retention of %s days' % (snapshot.id, snapshot.volume_id, delta.days, RETENTION))

    logger.info('Exiting.')
