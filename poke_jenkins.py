"""A simple extension that fires a Jenkins job for incoming heads."""
from contextlib import closing
from urllib import urlencode
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

    branches = {}

    # Collect the incoming heads that don't have any children.
    for rev in xrange(repo[node].rev(), len(repo)):
        ctx = repo[rev]
        branch = ctx.branch()
        if not any(ctx.children()):
            branches[branch] = ctx.hex()

    # For every head start a Jenkins job.
    for branch, rev in sorted(branches.items()):
        for job in jobs:
            base = urlparse.urljoin(jenkins_base_url, BUILD_URL.format(job=job))
            args = urlencode([('TAG', tag), ('NODE_ID', rev), ('REPO_URL', repo_url)])

            url = '?'.join([base, args])

            with closing(urllib2.urlopen(url, timeout=timeout)) as f:
                ui.write('Starting the job {job} for the branch: {branch}, revision: {rev}\n'.format(
                    job=job, branch=branch, rev=rev))
                f.read()
