"""A simple extension that fires a Jenkins job for incoming heads."""
from contextlib import closing
from urllib import urlencode
import re
import urllib2
import urlparse

from mercurial import util


BUILD_URL = 'job/{job}/buildWithParameters'


def reposetup(ui, repo):
    """Set up the Jenkins notification hook.

    :param ui: Mercurial ui object
    :param repo: Mercurial repository object
    """
    ui.setconfig("hooks", "changegroup.poke_jenkins", poke_jenkins_hook)


def poke_jenkins_hook(ui, repo, node, **kwargs):
    """Filter out the incoming heads and start a Jenkins job for them.

    :param ui: Mercurial ui object
    :param repo: Mercurial repository object
    :param node: Mercurial node object (eg commit)
    """
    jenkins_base_url = ui.config('poke_jenkins', 'jenkins_base_url', default=None, untrusted=False)
    if not jenkins_base_url:
        raise util.Abort(
            'You have to specify the parameter jenkins_base_url '
            'in the section poke_jenkins.'
        )

    timeout = int(ui.config('poke_jenkins', 'timeout', default=10, untrusted=False))

    repo_url = ui.config('poke_jenkins', 'repo_url', default=None, untrusted=False)
    if not repo_url:
        raise util.Abort(
            'You have to specify the parameter repo_url '
            'in the section poke_jenkins.'
        )

    jobs = ui.configlist('poke_jenkins', 'jobs', default=[], untrusted=False)
    tag = ui.config('poke_jenkins', 'tag', default='', untrusted=False)
    username = ui.config('poke_jenkins', 'username', default='', untrusted=False)
    password = ui.config('poke_jenkins', 'password', default='', untrusted=False)
    branch_regex = ui.config('poke_jenkins', 'branch_regex', default=None, untrusted=False)
    if branch_regex:
        branch_regex = re.compile(branch_regex)
    branches = {}

    # Collect the incoming heads that don't have any children.
    for rev in xrange(repo[node].rev(), len(repo)):
        ctx = repo[rev]
        branch = ctx.branch()
        if not any(ctx.children()):
            branches[branch] = ctx.hex()

    if username and password:
        headers = {
            'Authorization':
            'Basic: {0}'.format('{0}:{1}'.format(username, password).encode('base64').replace('\n', ''))
        }
    else:
        headers = {}

    # For every head start a Jenkins job.
    for branch, rev in sorted(branches.items()):
        if branch_regex is None or branch_regex.match(branch):
            for job in jobs:
                base = urlparse.urljoin(jenkins_base_url, BUILD_URL.format(job=job))
                args = urlencode([('TAG', tag), ('NODE_ID', rev), ('REPO_URL', repo_url), ('BRANCH', branch)])

                url = '?'.join([base, args])

                request = urllib2.Request(url, '', headers)

                with closing(urllib2.urlopen(request, timeout=timeout)) as f:
                    ui.write('Starting the job {job} for the branch: {branch}, revision: {rev}\n'.format(
                        job=job, branch=branch, rev=rev))
                    f.read()
