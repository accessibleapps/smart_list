from setuptools import setup, find_packages

__version__ = "0.2"
__doc__ = """Smart list view"""

setup(
 name = "smart_list",
 version = __version__,
 description = __doc__,
 packages=find_packages(),
 package_data = {
  'smart_list': ['iat_hook.dll'],
 },
 install_requires = [
  'frozendict',
  'resource_finder',
  'pypiwin32',
  #'wxpython',
 ],
 zip_safe = False,
 classifiers = [
  'Development Status :: 3 - Alpha',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'License :: OSI Approved :: MIT License',
  'Topic :: Software Development :: Libraries',
 ],
)
