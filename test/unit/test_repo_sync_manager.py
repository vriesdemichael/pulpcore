#!/usr/bin/python
#
# Copyright (c) 2011 Red Hat, Inc.
#
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

# Python
import copy
import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../common/")
import testutil

from pulp.common import dateutils
import pulp.server.content.manager as content_manager
from pulp.server.content.importer.base import Importer
from pulp.server.db.model.gc_repository import Repo, RepoImporter
import pulp.server.managers.repo.cud as repo_manager
import pulp.server.managers.repo.sync as repo_sync_manager

# -- mocks --------------------------------------------------------------------

class MockImporter(Importer):

    # Last call state
    repo_data = None
    importer_config = None
    sync_config = None
    sync_conduit = None

    # Call behavior
    raise_error = False

    def sync(self, repo_data, sync_conduit, importer_config, sync_config):

        # Store the contents of what was passed to the sync call at the class
        # level since the content manager factory will return a new instance
        # at each invocation of sync (which we can't get access to to look in)
        MockImporter.repo_data = repo_data
        MockImporter.importer_config = importer_config
        MockImporter.sync_config = sync_config
        MockImporter.sync_conduit = sync_conduit

        if MockImporter.raise_error:
            raise Exception('Something bad happened during sync')

    @classmethod
    def reset(cls):
        MockImporter.repo_data = None
        MockImporter.importer_config = None
        MockImporter.sync_config = None
        MockImporter.sync_conduit = None

        MockImporter.raise_error = False

# -- test cases ---------------------------------------------------------------

class RepoSyncManagerTests(testutil.PulpTest):

    def setUp(self):
        testutil.PulpTest.setUp(self)

        content_manager._create_manager()

        # Configure content manager
        content_manager._MANAGER.add_importer('MockImporter', 1, MockImporter, None)

        # Create the manager instances for testing
        self.repo_manager = repo_manager.RepoManager()
        self.sync_manager = repo_sync_manager.RepoSyncManager()

    def tearDown(self):
        testutil.PulpTest.tearDown(self)

        # Reset content manager
        content_manager._MANAGER.remove_importer('MockImporter', 1)

    def clean(self):
        testutil.PulpTest.clean(self)
        Repo.get_collection().remove()
        RepoImporter.get_collection().remove()

        # Reset the state of the mock's tracker variables
        MockImporter.reset()

    def test_sync(self):
        """
        Tests sync under normal conditions where everything is configured
        correctly. No importer config is specified.
        """

        # Setup
        sync_config = {'bruce' : 'hulk', 'tony' : 'ironman'}
        self.repo_manager.create_repo('repo-1')
        self.repo_manager.set_importer('repo-1', 'MockImporter', sync_config)

        # Test
        self.sync_manager.sync('repo-1', sync_config_override=None)

        # Verify
        repo = Repo.get_collection().find_one({'id' : 'repo-1'})
        repo_importer = RepoImporter.get_collection().find_one({'repo_id' : 'repo-1', 'id' : 'MockImporter'})

        #   Verify database
        self.assertTrue(not repo_importer['sync_in_progress'])
        self.assertTrue(repo_importer['last_sync'] is not None)
        self.assertTrue(assert_last_sync_time(repo_importer['last_sync']))

        #   Verify call into the importer
        self.assertEqual(repo['id'], MockImporter.repo_data['id'])
        self.assertEqual(sync_config, MockImporter.sync_config)
        self.assertTrue(MockImporter.sync_conduit is not None)

    def test_sync_with_sync_config_override(self):
        """
        Tests a sync when passing in an individual config of override options.
        """

        # Setup
        importer_config = {'thor' : 'thor'}
        self.repo_manager.create_repo('repo-1')
        self.repo_manager.set_importer('repo-1', 'MockImporter', importer_config)

        # Test
        sync_config_override = {'clint' : 'hawkeye'}
        self.sync_manager.sync('repo-1', sync_config_override=sync_config_override)

        # Verify
        repo = Repo.get_collection().find_one({'id' : 'repo-1'})
        repo_importer = RepoImporter.get_collection().find_one({'repo_id' : 'repo-1', 'id' : 'MockImporter'})

        #   Verify database
        self.assertTrue(not repo_importer['sync_in_progress'])
        self.assertTrue(repo_importer['last_sync'] is not None)
        self.assertTrue(assert_last_sync_time(repo_importer['last_sync']))

        #   Verify call into the importer
        self.assertEqual(repo['id'], MockImporter.repo_data['id'])
        self.assertTrue(MockImporter.sync_conduit is not None)

        merged = copy.copy(importer_config)
        merged.update(sync_config_override)
        self.assertEqual(merged, MockImporter.sync_config)

    def test_sync_missing_repo(self):
        """
        Tests the proper error is raised when a non-existent repo is specified.
        """

        # Test
        try:
            self.sync_manager.sync('fake-repo')
        except repo_sync_manager.MissingRepo, e:
            self.assertEqual('fake-repo', e.repo_id)
            print(e) # for coverage

    def test_sync_no_importer_set(self):
        """
        Tests the proper error is raised when no importer is set for the repo.
        """

        # Setup
        self.repo_manager.create_repo('importer-less') # don't set importer

        # Test
        try:
            self.sync_manager.sync('importer-less')
        except repo_sync_manager.NoImporter, e:
            self.assertEqual('importer-less', e.repo_id)
            print(e) # for coverage

    def test_sync_bad_importer(self):
        """
        Tests the proper error is raised when an importer is set on the repo but
        the importer is no longer present as a plugin. This situation simulates
        a case where a repo was once successfully configured but the server
        has since been bounced and the importer plugin removed.
        """

        # Setup
        self.repo_manager.create_repo('old-repo')
        self.repo_manager.set_importer('old-repo', 'MockImporter', None)

        #   Simulate bouncing the server and removing the importer plugin
        content_manager._MANAGER.remove_importer('MockImporter', 1)

        # Test
        try:
            self.sync_manager.sync('old-repo')
        except repo_sync_manager.MissingImporterPlugin, e:
            self.assertEqual('old-repo', e.repo_id)
            print(e) # for coverage

    def test_sync_bad_database(self):
        """
        Tests the case where the database got itself in a bad state where the
        repo thinks it has an importer but the importer-repo relationship doc
        doesn't exist in the database.
        """

        # Setup
        self.repo_manager.create_repo('good-repo')
        self.repo_manager.set_importer('good-repo', 'MockImporter', None)

        RepoImporter.get_collection().remove()

        # Test
        try:
            self.sync_manager.sync('good-repo')
        except repo_sync_manager.NoImporter, e:
            self.assertEqual('good-repo', e.repo_id)
            print(e) # for coverage

    def test_sync_with_error(self):
        """
        Tests a sync when the plugin raises an error.
        """

        # Setup
        MockImporter.raise_error = True

        self.repo_manager.create_repo('gonna-bail')
        self.repo_manager.set_importer('gonna-bail', 'MockImporter', {})

        # Test
        try:
            self.sync_manager.sync('gonna-bail')
        except repo_sync_manager.RepoSyncException, e:
            self.assertEqual('gonna-bail', e.repo_id)
            print(e) # for coverage

        # Verify
        repo_importer = RepoImporter.get_collection().find_one({'repo_id' : 'gonna-bail', 'id' : 'MockImporter'})

        self.assertTrue(not repo_importer['sync_in_progress'])
        self.assertTrue(repo_importer['last_sync'] is not None)
        self.assertTrue(assert_last_sync_time(repo_importer['last_sync']))

# -- testing utilities --------------------------------------------------------

def assert_last_sync_time(time_in_iso):
    now = datetime.datetime.now(dateutils.local_tz())
    finished = dateutils.parse_iso8601_datetime(time_in_iso)

    # Compare them within a threshold since they won't be exact
    difference = now - finished
    return difference.seconds < 2