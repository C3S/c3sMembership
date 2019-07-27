"""Test module for c3smembership.GitTools."""

import mock
import os
import re
import subprocess
import unittest

from c3smembership.git_tools import GitTools


class TestGitTools(unittest.TestCase):
    """Testing c3smembership.git_tools.GitTools.

    The testing of c3smembership.git_tools.GitTools is performed using the
    mock package to mock subprocess.
    """

    def __run_test(self, git_tools_method, std_pipe_values,
                   expected_commands, expected_result):
        """Provides an easy way to test GitTools methods encapsulating the
        mocking.

        GitTools methods usually use subprocess to execute git shell commands.
        This method mocks the subprocess calls and performs checks.
        """
        with mock.patch('c3smembership.git_tools.subprocess') as spmock:
            spmock.Popen.return_value.communicate.side_effect = \
                std_pipe_values
            spmock.PIPE = subprocess.PIPE
            method_result = git_tools_method()
            application_path = os.path.abspath(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '../../'))
            for expected_command in expected_commands:
                spmock.Popen.assert_any_call(
                    expected_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    cwd=application_path,
                    universal_newlines=True)
            self.assertEqual(len(expected_commands), spmock.Popen.call_count)
            self.assertEqual(method_result, expected_result)

    def __run_test_cases(self, git_tools_method, test_cases,
                         expected_commands):
        """Runs a set of defined test cases for testing git_tools methods.

        The git_tools_method is tested with each of the test_cases defining
        mock values for stdout and strerr values, expected result values and
        expected git commands to be executed.
        """
        for test_case in test_cases:
            self.__run_test(
                git_tools_method=git_tools_method,
                expected_commands=expected_commands,
                std_pipe_values=test_case['std_pipe_values'],
                expected_result=test_case['expected_result'])

    def test_get_commit_hash(self):
        """Test method GitTools.get_commit_hash().

        Test for success and failure. Mocking is used to simulate the
        behaviour of command line git.
        """
        test_cases = [
            # test success
            {
                'std_pipe_values': [(
                    '0123456789abcdefghijklmnopqrstuvwxyz\n',
                    '')],
                'expected_result': '0123456789abcdefghijklmnopqrstuvwxyz',
            },
            # test failure
            {
                'std_pipe_values': [('', 'fatal')],
                'expected_result': None
            },
        ]
        self.__run_test_cases(
            GitTools.get_commit_hash,
            test_cases,
            expected_commands=['git rev-parse HEAD'])

    def test_get_tag(self):
        """Test method GitTools.get_tag().

        Test for success and failure. Mocking is used to simulate the
        behaviour of command line git.
        """
        test_cases = [
            # test success
            {
                'std_pipe_values': [('v1.2.3-14-g0123456\n', '')],
                'expected_result': 'v1.2.3-14-g0123456',
            },
            # test failure
            {
                'std_pipe_values': [('', 'fatal')],
                'expected_result': None
            },
        ]
        self.__run_test_cases(
            GitTools.get_tag,
            test_cases,
            expected_commands=['git describe HEAD'])

    def test_get_github_base_url(self):
        """Test method GitTools.get_github_base_url().

        Test for success and failure. Mocking is used to simulate the
        behaviour of command line git.
        """
        test_cases = []
        # test success
        stdout_values = [
            'https://github.com/user/test123456789\n',
            'https://github.com/user/test123456789.git\n',
            'https://www.github.com/user/test123456789\n',
            'https://www.github.com/user/test123456789.git\n',
            'git://github.com/user/test123456789\n',
            'git://github.com/user/test123456789.git\n',
            'git://www.github.com/user/test123456789\n',
            'git://www.github.com/user/test123456789.git\n',
        ]
        for stdout_value in stdout_values:
            test_cases.append({
                'std_pipe_values': [(stdout_value, '')],
                'expected_result': 'https://github.com/user/test123456789'
            })
        # test failure
        test_cases.append({
            'std_pipe_values': [('', 'fatal')],
            'expected_result': None
        })
        self.__run_test_cases(
            GitTools.get_github_base_url,
            test_cases,
            expected_commands=['git config --get remote.origin.url'])

    def test_git_branch(self):
        """Test method GitTools.git_branch().

        Test for success and failure. Mocking is used to simulate the
        behaviour of command line git.
        """
        test_cases = [
            # test success
            {
                'std_pipe_values': [('testbranch\n', '')],
                'expected_result': 'testbranch',
            },
            # test failure
            {
                'std_pipe_values': [('', 'fatal')],
                'expected_result': None
            },
        ]
        self.__run_test_cases(
            GitTools.get_branch,
            test_cases,
            expected_commands=['git rev-parse --abbrev-ref HEAD'])

    def test_get_github_commit_url(self):
        """Test method GitTools.get_github_commit_url().

        Test for success and failure. Mocking is used to simulate the
        behaviour of command line git.
        """
        test_cases = [
            # test success
            {
                'std_pipe_values': [
                    # commit result
                    ('0123456789abcdefghijklmnopqrstuvwxyz\n', ''),
                    # git base url result
                    ('https://github.com/user/test123456789\n', '')
                ],
                'expected_result': (
                    'https://github.com/user/'
                    'test123456789/commit/0123456789abcdefgh'
                    'ijklmnopqrstuvwxyz')
            },
            # test failure: no commit
            {
                'std_pipe_values': [
                    ('', 'fatal'),
                    ('https://github.com/user/test123456789\n', '')
                ],
                'expected_result': None
            },
            # test failure: no origin remote
            {
                'std_pipe_values': [
                    ('0123456789abcdefghijklmnopqrstuvwxyz\n', ''),
                    ('', 'fatal')
                ],
                'expected_result': None
            },
        ]
        self.__run_test_cases(
            GitTools.get_github_commit_url,
            test_cases,
            expected_commands=[
                'git rev-parse HEAD',
                'git config --get remote.origin.url'])

    def test_get_github_branch_url(self):
        """Test method GitTools.get_github_branch_url().

        Test for success and failure. Mocking is used to simulate the
        behaviour of command line git.
        """
        test_cases = [
            # test success
            {
                'std_pipe_values': [
                    # branch result
                    ('testbranch\n', ''),
                    # git base url result
                    ('https://github.com/user/test123456789\n', '')
                ],
                'expected_result': (
                    'https://github.com/user/'
                    'test123456789/tree/testbranch')
            },
            # test failure: no commit
            {
                'std_pipe_values': [
                    ('', 'fatal'),
                    ('https://github.com/user/test123456789\n', '')
                ],
                'expected_result': None
            },
            # test failure: no origin remote
            {
                'std_pipe_values': [
                    ('testbranch', ''),
                    ('', 'fatal')
                ],
                'expected_result': None
            },
        ]
        self.__run_test_cases(
            GitTools.get_github_branch_url,
            test_cases,
            expected_commands=[
                'git rev-parse --abbrev-ref HEAD',
                'git config --get remote.origin.url'])

    def test_github_remote_regex(self):
        """Test regular expression GitTools.github_remote_regex.

        Parts of the regular expression are tested separately. Test are only
        done for success so far. Tests for failure could be added.
        """
        github_remote_test_values = [
            # test protocols
            {
                'value': 'git://github.com/myGithubUser123/test456Repository',
                'protocol': 'git',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': ('http://github.com/myGithubUser123/'
                          'test456Repository'),
                'protocol': 'http',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': ('https://github.com/myGithubUser123/'
                          'test456Repository'),
                'protocol': 'https',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': 'ftp://github.com/myGithubUser123/test456Repository',
                'protocol': 'ftp',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': ('ftps://github.com/myGithubUser123/'
                          'test456Repository'),
                'protocol': 'ftps',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': ('rsync://github.com/myGithubUser123/'
                          'test456Repository'),
                'protocol': 'rsync',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            # test ssh user
            {
                'value': ('ssh://user@github.com/myGithubUser123/'
                          'test456Repository'),
                'protocol': 'ssh',
                'ssh_user': 'user',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            # test subdomains
            {
                'value': ('ssh://subdomain.github.com/myGithubUser123/'
                          'test456Repository'),
                'protocol': 'ssh',
                'subdomain': 'subdomain',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': ('ssh://some.sub.domain.github.com/'
                          'myGithubUser123/test456Repository'),
                'protocol': 'ssh',
                'subdomain': 'some.sub.domain',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            # test ports
            {
                'value': ('ssh://github.com:1/myGithubUser123/'
                          'test456Repository'),
                'protocol': 'ssh',
                'port': '1',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': ('ssh://github.com:12/myGithubUser123/'
                          'test456Repository'),
                'protocol': 'ssh',
                'port': '12',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': ('ssh://github.com:123/myGithubUser123/'
                          'test456Repository'),
                'protocol': 'ssh',
                'port': '123',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': ('ssh://github.com:1234/myGithubUser123/'
                          'test456Repository'),
                'protocol': 'ssh',
                'port': '1234',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': ('ssh://github.com:65535/myGithubUser123/'
                          'test456Repository'),
                'protocol': 'ssh',
                'port': '65535',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            # test repository syntax
            {
                'value': ('ssh://github.com/myGithubUser123/'
                          'test456Repository/'),
                'protocol': 'ssh',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': ('ssh://github.com/myGithubUser123/'
                          'test456Repository.git'),
                'protocol': 'ssh',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
            {
                'value': ('ssh://github.com/myGithubUser123/'
                          'test456Repository.git/'),
                'protocol': 'ssh',
                'github_user': 'myGithubUser123',
                'github_repository': 'test456Repository'
            },
        ]
        pattern = re.compile(GitTools.github_remote_regex)
        for test_case in github_remote_test_values:
            match = pattern.search(test_case['value'])
            groupdict = match.groupdict()
            for group in groupdict:
                if groupdict[group] is not None:
                    self.assertTrue(group in test_case)
                    self.assertEqual(groupdict[group], test_case[group])
            for group in test_case:
                if group != 'value':
                    self.assertTrue(group in groupdict)
                    self.assertEqual(groupdict[group], test_case[group])
