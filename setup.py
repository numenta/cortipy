#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

sdict = {}

execfile('cortipy/version.py', {}, sdict)

def findRequirements():
  """
  Read the requirements.txt file and parse into requirements for setup's
  install_requirements option.
  """
  return [
    line.strip()
    for line in open("requirements.txt").readlines()
    if not line.startswith("#")
  ]

sdict.update({
    'name' : 'cortipy',
    'description' : 'Python client for REST API',
    'url': 'http://github.com/numenta/cortipy',
    'download_url' : 'https://pypi.python.org/packages/source/g/cortipy/cortipy-%s.tar.gz' % sdict['version'],
    'author' : 'Alexander Lavin',
    'author_email' : 'alavin@numenta.com',
    'keywords' : ['sdr', 'nlp', 'rest', 'htm', 'cortical.io'],
    'license' : 'MIT',
    'install_requires': findRequirements(),
    'test_suite': 'tests.unit',
    'packages' : ['cortipy'],
    'classifiers' : [
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python'],
})

setup(**sdict)
