from distutils.core import setup

__version__ = "0.1"
__doc__ = """Smart list view"""

setup(
 name = "smart_list",
 version = __version__,
 description = __doc__,
 py_modules = ["smart_list"],
 install_requires = [
  'frozendict',
  #'wxpython',
 ],
 classifiers = [
  'Development Status :: 3 - Alpha',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'License :: OSI Approved :: MIT License',
  'Topic :: Software Development :: Libraries',
 ],
)
