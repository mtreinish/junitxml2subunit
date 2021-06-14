# Copyright 2018 Matthew Treinish
#
# This file is part of junitxml2subunit
#
# junitxml2subunit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# junitxml2subunit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with junitxml2subunit.  If not, see <http://www.gnu.org/licenses/>.

import functools
import io
import os
import subprocess
import tempfile

import fixtures
import subunit
import testtools


class TestJunitXML2Subunit(testtools.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestJunitXML2Subunit, cls).setUpClass()
        cls.examples_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'examples'))
        test_dir = os.path.abspath(os.path.dirname(__file__))
        cls.repo_root = os.path.dirname(test_dir)
        subprocess.call(['cargo', 'build'], cwd=cls.repo_root)
        cls.command = os.path.join(cls.repo_root,
                                   'target/debug/junitxml2subunit')

    def setUp(self):
        super(TestJunitXML2Subunit, self).setUp()
        stdout = self.useFixture(fixtures.StringStream('stdout')).stream
        self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        stderr = self.useFixture(fixtures.StringStream('stderr')).stream
        self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))
        self.useFixture(fixtures.LoggerFixture(nuke_handlers=False,
                                               level=None))

    def _check_subunit(self, output_stream):
        stream = subunit.ByteStreamToStreamResult(output_stream)
        starts = testtools.StreamResult()
        summary = testtools.StreamSummary()
        tests = []

        def _add_dict(test):
            tests.append(test)

        outcomes = testtools.StreamToDict(functools.partial(_add_dict))
        result = testtools.CopyStreamResult([starts, outcomes, summary])
        result.startTestRun()
        try:
            stream.run(result)
        finally:
            result.stopTestRun()
        self.assertThat(len(tests), testtools.matchers.GreaterThan(0))
        return tests

    def test_ant_xml_in_stdout(self):
        ant_xml_path = os.path.join(self.examples_dir, 'ant.xml')
        junitxml_proc = subprocess.Popen([self.command, ant_xml_path],
                                         cwd=self.repo_root,
                                         stdout=subprocess.PIPE)
        stdout, _ = junitxml_proc.communicate()
        tests = self._check_subunit(io.BytesIO(stdout))
        self.assertEqual(1, len(tests))
        self.assertEqual('codereview.cobol.rules.ProgramIdRule',
                         tests[0].get('id'))
        self.assertEqual('fail', tests[0].get('status'))

    def test_ant_xml_in_file_out(self):
        ant_xml_path = os.path.join(self.examples_dir, 'ant.xml')
        out_file, out_path = tempfile.mkstemp()
        os.close(out_file)
        self.addCleanup(os.remove, out_path)
        junitxml_proc = subprocess.Popen([self.command, '-o', out_path,
                                          ant_xml_path],
                                         cwd=self.repo_root,
                                         stdout=subprocess.PIPE)
        stdout, _ = junitxml_proc.communicate()
        with open(out_path, 'r') as fd:
            tests = self._check_subunit(fd)
        self.assertEqual(1, len(tests))
        self.assertEqual('codereview.cobol.rules.ProgramIdRule',
                         tests[0].get('id'))
        self.assertEqual('fail', tests[0].get('status'))

    def test_hudson_xml_in_stdout(self):
        hudson_xml_path = os.path.join(self.examples_dir, 'hudson.xml')
        junitxml_proc = subprocess.Popen([self.command, hudson_xml_path],
                                         cwd=self.repo_root,
                                         stdout=subprocess.PIPE)
        stdout, _ = junitxml_proc.communicate()
        tests = self._check_subunit(io.BytesIO(stdout))
        self.assertEqual(3, len(tests))
        test_ids = [x.get('id') for x in tests]
        test_statuses = [x.get('status') for x in tests]
        self.assertIn('tests.ATest.error',
                      test_ids)
        self.assertIn('tests.ATest.fail', test_ids)
        self.assertIn('tests.ATest.success', test_ids)
        self.assertEqual(['fail', 'fail', 'success'], test_statuses)

    def test_hudson_xml_in_file_out(self):
        hudson_xml_path = os.path.join(self.examples_dir, 'hudson.xml')
        out_file, out_path = tempfile.mkstemp()
        os.close(out_file)
        self.addCleanup(os.remove, out_path)
        junitxml_proc = subprocess.Popen([self.command, '-o', out_path,
                                          hudson_xml_path],
                                         cwd=self.repo_root,
                                         stdout=subprocess.PIPE)
        stdout, _ = junitxml_proc.communicate()
        with open(out_path, 'r') as fd:
            tests = self._check_subunit(fd)
        self.assertEqual(3, len(tests))
        test_ids = [x.get('id') for x in tests]
        test_statuses = [x.get('status') for x in tests]
        self.assertIn('tests.ATest.error',
                      test_ids)
        self.assertIn('tests.ATest.fail', test_ids)
        self.assertIn('tests.ATest.success', test_ids)
        self.assertEqual(['fail', 'fail', 'success'], test_statuses)

    def test_pytest_xml_in_stdout(self):
        pytest_xml_path = os.path.join(self.examples_dir, 'pytest.xml')
        junitxml_proc = subprocess.Popen([self.command, pytest_xml_path],
                                         cwd=self.repo_root,
                                         stdout=subprocess.PIPE)
        stdout, _ = junitxml_proc.communicate()
        tests = self._check_subunit(io.BytesIO(stdout))
        self.assertEqual(118, len(tests))
        skip_count = len([x for x in tests if x.get('status') == 'skip'])
        success_count = len([x for x in tests if x.get('status') == 'success'])
        example_id = ('stestr.tests.test_scheduler.TestScheduler.'
                      'test_partition_tests_with_grouping')
        test_ids = [x.get('id') for x in tests]
        self.assertIn(example_id, test_ids)
        self.assertEqual(skip_count, 2)
        self.assertEqual(success_count, 116)

    def test_pytest_xml_in_file_out(self):
        pytest_xml_path = os.path.join(self.examples_dir, 'pytest.xml')
        out_file, out_path = tempfile.mkstemp()
        os.close(out_file)
        self.addCleanup(os.remove, out_path)
        junitxml_proc = subprocess.Popen([self.command, '-o', out_path,
                                          pytest_xml_path],
                                         cwd=self.repo_root,
                                         stdout=subprocess.PIPE)
        stdout, _ = junitxml_proc.communicate()
        with open(out_path, 'r') as fd:
            tests = self._check_subunit(fd)
        self.assertEqual(118, len(tests))
        test_ids = [x.get('id') for x in tests]
        skip_count = len([x for x in tests if x.get('status') == 'skip'])
        success_count = len([x for x in tests if x.get('status') == 'success'])
        example_id = ('stestr.tests.test_scheduler.TestScheduler.'
                      'test_partition_tests_with_grouping')
        self.assertIn(example_id, test_ids)
        self.assertEqual(skip_count, 2)
        self.assertEqual(success_count, 116)

    def test_no_time_xml_in_stdout(self):
        no_time_xml_path = os.path.join(self.examples_dir, 'no_time.xml')
        junitxml_proc = subprocess.Popen([self.command, no_time_xml_path],
                                         cwd=self.repo_root,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         encoding='utf8')
        _, stderr = junitxml_proc.communicate()
        self.assertEqual(2, junitxml_proc.returncode)
        self.assertEqual(
            "Invalid XML: There is no time attribute on a testcase",
            stderr.strip())

    def test_no_time_xml_in_file_out(self):
        no_time_xml_path = os.path.join(self.examples_dir, 'no_time.xml')
        out_file, out_path = tempfile.mkstemp()
        os.close(out_file)
        self.addCleanup(os.remove, out_path)
        junitxml_proc = subprocess.Popen([self.command, '-o', out_path,
                                          no_time_xml_path],
                                         cwd=self.repo_root,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         encoding='utf8')
        _, stderr = junitxml_proc.communicate()
        self.assertEqual(2, junitxml_proc.returncode)
        self.assertEqual(
            "Invalid XML: There is no time attribute on a testcase",
            stderr.strip())

    def test_no_id_xml_in_stdout(self):
        no_id_xml_path = os.path.join(self.examples_dir, 'no_id.xml')
        junitxml_proc = subprocess.Popen([self.command, no_id_xml_path],
                                         cwd=self.repo_root,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         encoding='utf8')
        _, stderr = junitxml_proc.communicate()
        self.assertEqual(3, junitxml_proc.returncode)
        self.assertEqual(
            "Invalid XML: There is no testname or classname attribute on a "
            "testcase",
            stderr.strip())

    def test_no_id_xml_in_file_out(self):
        no_id_xml_path = os.path.join(self.examples_dir, 'no_id.xml')
        out_file, out_path = tempfile.mkstemp()
        os.close(out_file)
        self.addCleanup(os.remove, out_path)
        junitxml_proc = subprocess.Popen([self.command, '-o', out_path,
                                          no_id_xml_path],
                                         cwd=self.repo_root,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         encoding='utf8')
        _, stderr = junitxml_proc.communicate()
        self.assertEqual(3, junitxml_proc.returncode)
        self.assertEqual(
            "Invalid XML: There is no testname or classname attribute on a "
            "testcase",
            stderr.strip())

    def test_missing_file(self):
        out_file, out_path = tempfile.mkstemp()
        os.close(out_file)
        os.remove(out_path)
        junitxml_proc = subprocess.Popen([self.command, out_path],
                                         cwd=self.repo_root,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         encoding='utf8')
        _, stderr = junitxml_proc.communicate()
        self.assertEqual(1, junitxml_proc.returncode)
        self.assertEqual(
            "Path to XML file: %s does not exist" % out_path, stderr.strip())
