"""Tests for poke_jenkins hook."""
import contextlib
import os
import tempfile
import urllib

import mock
import pytest

from mercurial import ui, hg, util, commands

import poke_jenkins


@pytest.fixture
def hg_ui():
    """Create test mercurial ui."""
    return ui.ui()


@pytest.fixture
def jenkins_base_url():
    """Get test jenkins base url."""
    return 'http://example.ci.com/'


@pytest.fixture
def repo_url():
    """Get test repo url."""
    return 'ssh://code.example.com/users/foo'


@pytest.fixture
def hg_ui_with_jenkins_base_url(hg_ui, jenkins_base_url):
    """Get test mercurial ui with jenkins base url config set up."""
    hg_ui.setconfig('poke_jenkins', 'jenkins_base_url', jenkins_base_url)
    return hg_ui


@pytest.fixture
def hg_ui_with_repo_url(hg_ui, repo_url):
    """Get test mercurial ui with jenkins repo url config set up."""
    hg_ui.setconfig('poke_jenkins', 'repo_url', repo_url)
    return hg_ui


@pytest.fixture
def jenkins_jobs():
    """Get test jenkins jobs."""
    return ['unit', 'functional']


@pytest.fixture
def jenkins_username():
    """Get test jenkins username."""
    return 'foo'


@pytest.fixture
def jenkins_password():
    """Get test jenkins password."""
    return 'bar'


@pytest.fixture
def hg_ui_with_jenkins_jobs(hg_ui, jenkins_jobs):
    """Get test mercurial ui with jenkins jobs config set up."""
    hg_ui.setconfig('poke_jenkins', 'jobs', jenkins_jobs)
    return hg_ui


@pytest.fixture
def hg_ui_with_jenkins_auth(hg_ui, jenkins_username, jenkins_password):
    """Get test mercurial ui with jenkins auth config set up."""
    hg_ui.setconfig('poke_jenkins', 'username', jenkins_username)
    hg_ui.setconfig('poke_jenkins', 'password', jenkins_password)
    return hg_ui


@pytest.fixture
def hg_ui_with_branch_regex(hg_ui, jenkins_username, jenkins_password):
    """Get test mercurial ui with branch regex config set up."""
    hg_ui.setconfig('poke_jenkins', 'branch_regex', '^c\d{4}')
    return hg_ui


@pytest.fixture
def tag():
    """Get test tag."""
    return 'some_tag'


@pytest.fixture
def hg_ui_with_tag(hg_ui, tag):
    """Get test mercurial ui with tag config set up."""
    hg_ui.setconfig('poke_jenkins', 'tag', tag)
    return hg_ui


@pytest.fixture
def repo_dir():
    """Get test repo dir."""
    return tempfile.mkdtemp()


@pytest.fixture
def file_path(repo_dir):
    """Get test file path."""
    return os.path.join(repo_dir, 'file1.txt')


@pytest.fixture
def hg_repo(hg_ui, repo_dir):
    """Get test mercurial repo."""
    commands.init(hg_ui, repo_dir)
    return hg.repository(hg_ui, repo_dir)


@pytest.fixture
def hg_node(hg_repo, hg_ui, file_path):
    """Get test mercurial node. We make commits to have it."""
    with contextlib.closing(open(file_path, 'a')) as f:
        f.write('some')
    commands.commit(hg_ui, hg_repo, file_path, message="A test", addremove=True)

    with contextlib.closing(open(file_path, 'a')) as f:
        f.write('another')

    commands.commit(hg_ui, hg_repo, file_path, message="A test", addremove=True)
    return 1


def test_poke_jenkins(hg_ui, hg_repo):
    """Test poke_jenkins hook setup."""
    poke_jenkins.reposetup(hg_ui, hg_repo)
    assert hg_ui.config('hooks', 'changegroup.poke_jenkins') == poke_jenkins.poke_jenkins_hook


def test_poke_jenkins_hook_no_jenkins_base_url(hg_ui, hg_repo, hg_node):
    """Test poke_jenkins hook without url being set up."""
    with pytest.raises(util.Abort) as exc:
        # should raise an exception to set up the jenkins base url
        poke_jenkins.poke_jenkins_hook(hg_ui, hg_repo, hg_node)

    assert exc.value.args == ('You have to specify the parameter jenkins_base_url in the section poke_jenkins.',)


def test_poke_jenkins_hook_no_repo_url(hg_ui_with_jenkins_base_url, hg_repo, hg_node):
    """Test poke_jenkins hook with jenkins base url being set up but without repo_url."""
    with pytest.raises(util.Abort) as exc:
        # should raise an exception to set up the hook url
        poke_jenkins.poke_jenkins_hook(hg_ui_with_jenkins_base_url, hg_repo, hg_node)

    assert exc.value.args == ('You have to specify the parameter repo_url in the section poke_jenkins.',)


def test_poke_jenkins_hook(
        hg_ui_with_repo_url, hg_ui_with_jenkins_base_url, hg_ui_with_jenkins_jobs, hg_ui_with_tag, hg_repo,
        hg_node, repo_url, tag):
    """Test poke_jenkins hook with jenkins base url and repo url and jenkins jobs being set up."""
    with mock.patch.multiple('urllib2', urlopen=mock.DEFAULT, Request=mock.DEFAULT) as mocks:
        poke_jenkins.poke_jenkins_hook(hg_ui_with_jenkins_jobs, hg_repo, hg_node)
        node_id = hg_repo[hg_node].hex()
        mocks['Request'].assert_has_calls((
            mock.call(
                'http://example.ci.com/job/unit/buildWithParameters?TAG={tag}&NODE_ID={node_id}&{repo_url}'
                '&BRANCH={branch}'.format(
                    repo_url=urllib.urlencode(dict(REPO_URL=repo_url)),
                    node_id=node_id, tag=tag, branch='default'), '',
                {}),
            mock.call(
                'http://example.ci.com/job/functional/buildWithParameters?TAG={tag}&NODE_ID={node_id}&'
                '{repo_url}&BRANCH={branch}'.format(
                    repo_url=urllib.urlencode(dict(REPO_URL=repo_url)),
                    node_id=node_id, tag=tag, branch='default'), '',
                {}),
        ), any_order=True)


def test_poke_jenkins_hook_with_auth(
        hg_ui_with_repo_url, hg_ui_with_jenkins_base_url, hg_ui_with_jenkins_jobs, hg_ui_with_jenkins_auth,
        hg_ui_with_tag, hg_repo, hg_node, repo_url, tag):
    """Test poke_jenkins hook with jenkins base url and repo url and jenkins jobs being set up and with auth enabled."""
    with mock.patch.multiple('urllib2', urlopen=mock.DEFAULT, Request=mock.DEFAULT) as mocks:
        poke_jenkins.poke_jenkins_hook(hg_ui_with_jenkins_jobs, hg_repo, hg_node)
        node_id = hg_repo[hg_node].hex()
        mocks['Request'].assert_has_calls((
            mock.call(
                'http://example.ci.com/job/unit/buildWithParameters?TAG={tag}&NODE_ID={node_id}&{repo_url}'
                '&BRANCH={branch}'.format(
                    repo_url=urllib.urlencode(dict(REPO_URL=repo_url)),
                    node_id=node_id, tag=tag, branch='default'), '',
                {'Authorization': 'Basic Zm9vOmJhcg=='}),
            mock.call(
                'http://example.ci.com/job/functional/buildWithParameters?TAG={tag}&NODE_ID={node_id}&'
                '{repo_url}&BRANCH={branch}'.format(
                    repo_url=urllib.urlencode(dict(REPO_URL=repo_url)),
                    node_id=node_id, tag=tag, branch='default'), '',
                {'Authorization': 'Basic Zm9vOmJhcg=='}),
        ), any_order=True)


def test_poke_jenkins_hook_with_branch_regex(
        hg_ui_with_repo_url, hg_ui_with_jenkins_base_url, hg_ui_with_jenkins_jobs, hg_ui_with_branch_regex,
        hg_ui_with_tag, hg_repo, hg_node, repo_url, tag):
    """Test poke_jenkins hook with jenkins base url and repo url and jenkins jobs being set up and with auth enabled."""
    with mock.patch.multiple('urllib2', urlopen=mock.DEFAULT, Request=mock.DEFAULT) as mocks:
        poke_jenkins.poke_jenkins_hook(hg_ui_with_jenkins_jobs, hg_repo, hg_node)
        mocks['Request'].assert_has_calls((), any_order=True)
