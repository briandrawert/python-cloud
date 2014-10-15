#!/usr/bin/env python

import os
import sys
import shutil

#fix a bug that setuptools creates:
import distutils.filelist
findall = distutils.filelist.findall  
from distutils.util import change_root, convert_path
from distutils.dir_util import mkpath
from distutils.file_util import copy_file

# For future use. Always will be true currently as we require setuptools
use_setuptools = False

def abort(msg):    
    print >> sys.stderr, msg
    sys.exit(1)


if sys.argv == ['setup.py', 'sdist']:
    print 'using regular setup tools'
    from distutils.core import setup
else:
    try:    
        from setuptools import setup
        distutils.filelist.findall = findall #reset
        use_setuptools = True
    except ImportError:
        abort('Distribute not installed. Cannot continue with installation. Get Distribute from http://pypi.python.org/pypi/distribute')

# bring in release_version
basedir = os.path.split(__file__)[0]

for line in open(os.path.join(basedir, 'src/versioninfo.py')).readlines():
    if (line.startswith('release_version')):
        exec(line.strip())
        

if sys.version < '2.6':
    abort('Python must be > 2.6 to use PiCloud')
elif sys.version > '3':
    abort('This package cannot be used under Python3. Please get the Python3 package from http://www.picloud.com')


#Python2.5 lacks important packages like ssl and (simple)json. Discover if needed
requires = []
data_files = []
scripts = []
options = {}

#source install deps checking
try:
    import json
except ImportError:
    try:
        import simplejson
    except ImportError:
        if not use_setuptools:        
            abort('simplejson must be installed to use picloud\nDownload it at http://pypi.python.org/pypi/simplejson/')
        else:
            requires.append("simplejson")
            
try:
    import ssl
except ImportError:
    try:
        import OpenSSL
    except ImportError:
        if not use_setuptools:
            abort('OpenSSL python bindings not installed.  These are required to ensure a secure connection to Picloud.\nDownload them at http://pypi.python.org/pypi/ssl')
        else: #inject requirement
            requires.append('ssl')

#check for pywin32 on windows which is highly recommended:
#These can't be installed automatically, so just warn
if os.name == 'nt':
    try: 
        import win32con
    except ImportError:
        sys.stderr.write('Python for Windows extensions are highly recommended for using picloud.\nDownload them at http://sourceforge.net/projects/pywin32/')

if 'bdist_wininst' in sys.argv:
    # hot patch for bdist_wininst

    import distutils.command.bdist_wininst as bwin
    def get_exe_bytes (self):
        # Aaron's hack fix
        
        bv = 9.0
        if self.plat_name == 'win-amd64':
            sfix = '-amd64'
        else:
            sfix = ''
        directory = os.path.dirname(bwin.__file__)
        filename = os.path.join(directory, "wininst-%.1f%s.exe" % (bv, sfix))
        print 'using %s' % filename
        try:
            f = open(filename, "rb")
        except IOError, msg:
            from distutils.errors import DistutilsFileError
            raise DistutilsFileError, str(msg) + ', please install the python%s-dev package' % sys.version[:3]
        try:
            return f.read()
        finally:
            f.close()
            
    def get_installer_filename(self, fullname):
        # from http://bugs.python.org/issue8954
        
        # Factored out to allow overriding in subclasses

        # pure Python packages always have win32 extension
        # required for crossplatform behaviour
        if (not self.distribution.has_ext_modules() and 
            not self.distribution.has_c_libraries() and
            self.plat_name != 'win-amd64'):
            basename = "%s.%s" % (fullname, "win32")
        else:
            basename = "%s.%s" % (fullname, self.plat_name)

        if self.target_version:
            # if we create an installer for a specific python version,
            # it's better to include this in the name
            installer_name = os.path.join(self.dist_dir,
                                          "%s-py%s.exe" %
                                          (basename, self.target_version))
        else:
            installer_name = os.path.join(self.dist_dir, "%s.exe" % basename)
        return installer_name          
     
    bwin.bdist_wininst.get_exe_bytes = get_exe_bytes
    bwin.bdist_wininst.get_installer_filename = get_installer_filename
    
    if '--plat-name=win32' in sys.argv:
        distribute_file_path = 'extra/distribute-0.6.26.win32.msi'
    elif '--plat-name=win-amd64' in sys.argv:
        distribute_file_path = 'extra/distribute-0.6.26.win-amd64.msi'

    rsync_dir = 'extra/rsync'
    rsync_files = [os.path.join(rsync_dir, f) for f in os.listdir(rsync_dir)]
    #rsync_install_dir = os.path.join(sys.prefix, 'lib', 'site-packages',
    #                                 'cloud', 'extras')

    data_files = [('scripts', [distribute_file_path]),
                  ('extras', rsync_files)]
    scripts = ['post_install.py']
    options = { 'bdist_wininst': {'install_script':'post_install.py'} }
    
    
    """hot fix for setuptools
    This script is for 32-bit so should always work"""
    from setuptools.command.easy_install import get_script_header, sys_executable, is_64bit, resource_string
    import re
       
    def get_script_args(dist, executable=sys_executable, wininst=False):
        """Yield write_script() argument tuples for a distribution's entrypoints"""
        spec = str(dist.as_requirement())
        header = get_script_header("", executable, wininst)
        for group in 'console_scripts', 'gui_scripts':
            for name, ep in dist.get_entry_map(group).items():
                script_text = (
                    "# EASY-INSTALL-ENTRY-SCRIPT: %(spec)r,%(group)r,%(name)r\n"
                    "__requires__ = %(spec)r\n"
                    "import sys\n"
                    "from pkg_resources import load_entry_point\n"
                    "\n"
                    "if __name__ == '__main__':"
                    "\n"
                    "    sys.exit(\n"
                    "        load_entry_point(%(spec)r, %(group)r, %(name)r)()\n"
                    "    )\n"
                ) % locals()
                if sys.platform=='win32' or wininst:
                    # On Windows/wininst, add a .py extension and an .exe launcher
                    if group=='gui_scripts':
                        ext, launcher = '-script.pyw', 'gui.exe'
                        old = ['.pyw']
                        new_header = re.sub('(?i)python.exe','pythonw.exe',header)
                    else:
                        ext, launcher = '-script.py', 'cli.exe'
                        old = ['.py','.pyc','.pyo']
                        new_header = re.sub('(?i)pythonw.exe','python.exe',header)
                    
                    if (sys.platform=='win32' and is_64bit()) or ('--plat-name=win-amd64' in sys.argv):
                        launcher = launcher.replace(".", "-64.")
                    else: # on linux (build system) always fall back to this
                        launcher = launcher.replace(".", "-32.")
                    if os.path.exists(new_header[2:-1]) or sys.platform!='win32':
                        hdr = new_header
                    else:
                        hdr = header
                    yield (name+ext, hdr+script_text, 't', [name+x for x in old])
                    yield (
                        name+'.exe', resource_string('setuptools', launcher),
                        'b' # write in binary mode
                    )
                else:
                    # On other platforms, we assume the right thing to do is to
                    # just write the stub with no extension.
                    yield (name, header+script_text)

    import setuptools.command.easy_install
    setuptools.command.easy_install.get_script_args = get_script_args

    

requires.append('setuptools')

dist = setup(
    name='cloud',
    version=release_version,  #defined by versioninfo.py exec
    description='PiCloud client-side library',      
    author='PiCloud, Inc.',
    author_email='contact@picloud.com',
    url='http://www.picloud.com',
    install_requires=requires,
    license='GNU LGPL',
    long_description=open('README.txt').read(),
    packages=['cloud', 'cloud.cli', 'cloud.serialization', 'cloud.transport', 'cloud.util', 'cloud.util.cloghandler', 'cloud.shortcuts'],
    package_dir = {'cloud': os.path.join(basedir, 'src')},
    package_data= {'cloud.util.cloghandler' : ['README, PKG-INFO, LICENSE']}, 
    platforms=['CPython 2.6', 'CPython 2.7'],      
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Networking',
        ],
    entry_points={'console_scripts': ['picloud = cloud.cli.main:main',]},
    data_files = data_files,
    scripts = scripts,
    options = options
    )


if 'install' in sys.argv and '--single-version-externally-managed' not in sys.argv:
    if os.name != 'nt':
        
        prefix = os.path.normpath(sys.prefix)
        root = None
        try:
            installer = dist.command_obj['install']
            prefix = installer.prefix
            root = installer.root
        except Exception:
            pass        
        
        # Try to install manpage and bash scripts:
        extra_files = [
                 {'src' : 'bash_completion.d/picloud',
                 'dst' : '/etc/bash_completion.d/',
                 'name' : 'bash completion scripts'},
                 {'src' : 'doc/picloud.1',
                 'dst' : '%s/share/man/man1/' % prefix,
                 'name' : 'PiCloud manpage'}
                 ]                         
        # copy code borrowed from distutils.command.install_data
        # We can't use original as it raises an exception if the file cant be written;
        # on error we just want to warn as these files aren't essential
        for file_info in extra_files:
            try:
                dst = convert_path(file_info['dst'])
                if root:
                    dst = change_root(root, dst)
                
                if root: 
                    # directories generally expected to exist already; if not we have wrong target directory
                    # for package maintainers using root, just build it to temporary directory
                    mkpath(dst)
                
                src = convert_path(file_info['src'])
                copy_file(src, dst)
            except (OSError, IOError, distutils.errors.DistutilsError), e:
                sys.stderr.write('Warning: Could not install %s to %s\n' % (file_info['name'], str(e)))                
        
    
    print ''
    print '********************************************************'
    print '********************************************************'
    print '***                                                  ***'
    print '***  Please run "picloud setup" to complete install  ***'
    if os.name == 'nt':
        print '*** picloud.exe is in the Scripts directory of Python***'            
    print '***                                                  ***'
    print '********************************************************'
    print '********************************************************'
    print ''
