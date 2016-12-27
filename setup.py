from setuptools import setup, find_packages
import platform
__version__ = "0.2"
is_windows = platform.system() == 'Windows'

__doc__ = """Smart list view"""

install_requires = [
  'frozendict',
  'resource_finder',
  #'wxpython',
 ]
if is_windows:
	install_requires.append('pypiwin32')

setup(
 name = "smart_list",
 version = __version__,
 description = __doc__,
 packages=find_packages(),
 package_data = {
  'smart_list': ['iat_hook.dll'],
 },
 install_requires = install_requires,

 zip_safe = False,
 classifiers = [
  'Development Status :: 3 - Alpha',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'License :: OSI Approved :: MIT License',
  'Topic :: Software Development :: Libraries',
 ],
)
