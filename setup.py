#!/usr/bin/python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

sdict = {}

execfile('cortipy/version.py', {}, sdict)

sdict.update({
    'name' : 'cortipy',
    'description' : 'Python client for REST API',
    'url': 'http://github.com/numenta/cortipy',
    'download_url' : 'https://pypi.python.org/packages/source/g/cortipy/cortipy-%s.tar.gz' % sdict['version'],
    'author' : 'Alexander Lavin',
    'author_email' : 'alavin@numenta.com',
    'keywords' : ['sdr', 'nlp', 'rest', 'htm', 'cortical.io'],
    'license' : 'MIT',
    'install_requires': [
        'requests',
        'nose',
        'coverage',
        'httpretty'],
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
