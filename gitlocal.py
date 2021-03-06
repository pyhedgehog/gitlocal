#!/usr/bin/env python
import os
import sys
import pprint
import argparse
import traceback
import subprocess

debug = [__name__,'gitlocal'][__name__=='__main__'] in os.environ.get('PY_DEBUG','').lower().split(',')

def main(argv):
    global debug
    if debug: print('debug enabled')
    root = getconfig(True) or '/gitroot'
    if debug: print('default root = '+repr(root))
    p = argparse.ArgumentParser(prog=argv[0], description='git local')
    p.add_argument('--gitroot', default=root, help='Path to git local storage')
    p.add_argument('--debug', default=debug, action='store_true', help='Enable debug output')
    cmds = p.add_subparsers(title='subcommands', description='known subcommands', help='sub-command help')
    cmdconfig = cmds.add_parser('config', help='git local config subcommand')
    cmdconfig.add_argument('gitroot', help='Path to git local storage')
    cmdconfig.set_defaults(func=doconfig)
    cmdinit = cmds.add_parser('init', help='git local init subcommand')
    cmdinit.add_argument('--remote', default='origin', help='Name of the git remote')
    cmdinit.set_defaults(func=doinit)
    cmdclone = cmds.add_parser('clone', help='git local clone subcommand')
    cmdclone.add_argument('gitname', help='Name of git in local storage')
    cmdclone.set_defaults(func=doclone)
    cmdhelp = cmds.add_parser('help', help='git local help subcommand')
    cmdhelp.set_defaults(func=dohelp)
    #cmdtest = cmds.add_parser('test', help='git local test subcommand')
    #cmdtest.set_defaults(func=dotest)
    p.set_defaults(parser=p)
    args = p.parse_args(argv[1:])
    if args.debug and not debug: print('debug enabled')
    debug = args.debug
    return args.func(args)

def dohelp(args):
    try: args.parser.parse_args(['--help'])
    except SystemExit: pass
    for cmd in 'init config'.split():
        try: args.parser.parse_args([cmd, '--help'])
        except SystemExit: pass
    return 0

def dotest(args):
    print('\n'.join('%s=%s' % item for item in sorted(os.environ.items())))

def doclone(args):
    ensureconfig(args.gitroot)
    gitname = args.gitname
    if os.path.splitext(gitname)[1] != '.git': gitname += '.git'
    gitremote = os.path.join(args.gitroot, gitname)
    subprocess.check_call('git clone'.split()+[gitremote])

def getworktree():
    if 'GIT_WORK_TREE' in os.environ:
        gitpath = os.environ['GIT_WORK_TREE']
    else:
        gitpath = os.getcwd()
    if not os.path.exists(os.path.join(gitpath, '.git', 'config')):
        gitpath = None
    return gitpath

def doinit(args):
    gitpath = getworktree()
    if not gitpath:
        gitpath = os.getcwd()
        subprocess.check_call('git init'.split())
    ensureconfig(args.gitroot)
    gitname = os.path.basename(gitpath)
    if os.path.splitext(gitname)[1] != '.git': gitname += '.git'
    gitremote = os.path.join(args.gitroot, gitname)
    try:
        remote = subprocess.check_output(('git remote get-url '+args.remote).split(), stderr=open(os.devnull,'w')).rstrip('\n\r')
    except Exception:
        if debug: traceback.print_exc()
        remote = None
    if remote is not None and remote != gitremote:
        print(doinit_remote_errorpage % dict(remote=args.remote, url=remote))
        return 1
    if not os.path.exists(os.path.join(gitremote, 'config')):
        subprocess.check_call('git init --bare'.split()+[gitremote])
    if remote is None:
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

def run_subprocess(func, args, skiperr=False):
    stderr = None
    if skiperr and not debug: stderr = open(os.devnull,'w')
    try: return subprocess.check_output('git config --get local.storage'.split(), stderr=stderr)
    except Exception:
        if not skiperr: raise
        if debug: traceback.print_exc()
    return None

def getconfig(skiperr=False):
    root = run_subprocess(subprocess.check_output, 'git config --get local.storage'.split(), skiperr)
    if root is None:
        root = ''
    root = root.rstrip('\n\r')
    if debug: print('getconfig root = '+repr(root))
    return root

def sameconfig(gitroot, skiperr=False):
    return getconfig(skiperr) == gitroot

def setconfig(gitroot, target='--local', skiperr=False):
    run_subprocess(subprocess.check_call, ('git config '+target+' --replace-all local.storage').split()+[gitroot], skiperr)

def ensureconfig(gitroot):
    if sameconfig(gitroot, True): return
    gitpath = getworktree()
    if gitpath: setconfig(gitroot)

def doconfig(args):
    # FIXME: How to get path to my alias (ln <git cloned gitlocal.py> to /usr/local/bin/gitlocal or alike)
    # TODO: git config --global --replace-all alias.local "!gitlocal"
    try:
        if sameconfig(args.gitroot): return 0
    except Exception:
        if debug: traceback.print_exc()
        setconfig(args.gitroot, '--system', True)
        if sameconfig(args.gitroot, True): return 0
        setconfig(args.gitroot, '--global')
        if sameconfig(args.gitroot, True): return 0
    setconfig(args.gitroot, '--local')

if __name__=='__main__':
    sys.exit(main(sys.argv))
