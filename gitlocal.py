#!/usr/bin/env python
import os
import sys
import pprint
import argparse
import traceback
import subprocess

def main(argv):
    try: root = subprocess.check_output('git config --get local.storage')
    except Exception: root = '/gitroot'
    p = argparse.ArgumentParser(prog=argv[0], description='git local')
    p.add_argument('--gitroot', default=root, help='Path to git local storage.')
    cmds = p.add_subparsers(title='subcommands', description='known subcommands', help='sub-command help')
    cmdconfig = cmds.add_parser('config', help='git local config subcommand')
    cmdconfig.add_argument('gitroot', help='Path to git local storage.')
    cmdconfig.set_defaults(func=doconfig)
    cmdinit = cmds.add_parser('init', help='git local init subcommand')
    cmdinit.add_argument('--remote', default='origin', help='Name of the git remote')
    cmdinit.set_defaults(func=doinit)
    cmdhelp = cmds.add_parser('help', help='git local help subcommand')
    cmdhelp.set_defaults(func=dohelp)
    cmdtest = cmds.add_parser('test', help='git local test subcommand')
    cmdtest.set_defaults(func=dotest)
    p.set_defaults(parser=p)
    args = p.parse_args(argv[1:])
    return args.func(args)

def dohelp(args):
    try: args.parser.parse_args(['--help'])
    except SystemExit: pass
    for cmd in 'init config'.split():
        try: args.parser.parse_args([cmd, '--help'])
        except SystemExit: pass
    return 0

def dotest(args):
    print '\n'.join('%s=%s' % item for item in os.environ.items())

def doinit(args):
    if 'GIT_WORK_TREE' in os.environ:
        gitpath = os.environ['GIT_WORK_TREE']
    else:
        subprocess.check_call('git init'.split())
        gitpath = os.getcwd()
    ensureconfig(args.gitroot)
    gitname = os.path.basename(gitpath)
    if os.path.splitext(gitname)[1] != '.git': gitname += '.git'
    gitremote = os.path.join(args.gitroot, gitname)
    try:
        remote = subprocess.check_output(('git remote get-url '+args.remote).split(), stderr=open(os.devnull,'w')).rstrip('\n\r')
    except Exception:
        #traceback.print_exc()
        remote = None
    if remote is not None:
        if remote == gitremote: return 0
        print doinit_remote_errorpage % dict(remote=args.remote, url=remote)
    subprocess.check_call('git remote add'.split()+[args.remote, gitremote])

doinit_remote_errorpage = '''
ERROR: the remote "%(remote)s" already exists.

Are you trying to run gitlocal in a directory that already has a git
repository? This would overwrite your existing remote, which points to:

  %(url)s

If you've previously run gitlocal in this directory and you want to update
the contents of this git, just push to the existing git remote:

  git push

If you don't need this remote anymore (say, if you cloned someone else's
gist), gistup will replace it with a new one if you first run:

  git remote rm %(remote)s

Lastly, you can also specify a different remote name for gitlocal, so that
you can push to multiple git remotes:

  git local --remote=local

Please do one of the above and try again.
'''

def sameconfig(gitroot):
    root = subprocess.check_output('git config --get local.storage'.split())
    return root.rstrip('\n\r') == gitroot

def setconfig(gitroot, target='--local'):
    subprocess.check_call(('git config '+target+' --replace-all local.storage').split()+[gitroot])

def ensureconfig(gitroot):
    try:
        if sameconfig(gitroot): return
    except Exception: pass
    setconfig(args.gitroot)

def doconfig(args):
    # FIXME: How to get path to my alias (ln <git cloned gitlocal.py> to /usr/local/bin/gitlocal or alike)
    # TODO: git config --global --add alias.local "!gitlocal"
    try:
        if sameconfig(args.gitroot): return 0
    except Exception:
        try:
            setconfig(args.gitroot, '--system')
            if sameconfig(args.gitroot): return 0
        except Exception: pass
        setconfig(args.gitroot, '--global')
        try:
            if sameconfig(args.gitroot): return 0
        except Exception: pass
    setconfig(args.gitroot, '--local')

if __name__=='__main__':
    sys.exit(main(sys.argv))
