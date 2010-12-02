#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
	name='TracGoogleAppsAuthPlugin',
	version='0.2.2',
	author='David A. Riggs',
	author_email='david.riggs@createtank.com',
	url='http://code.google.com/p/tracgoogleappsauthplugin/',
	download_url='http://code.google.com/p/tracgoogleappsauthplugin/',
	description='Trac authentication plugin for integration with hosted Google Apps domain',
	long_description=open('README.txt').read(),
	packages=find_packages(exclude=['*.tests*']),
	entry_points = '''
		[trac.plugins]
		googleappsauthplugin = createtank.trac.googleauth
	''',
	classifiers=[
				'Development Status :: 3 - Alpha',
				'Environment :: Plugins',
				'Framework :: Trac',
				'Intended Audience :: System Administrators',
				'License :: OSI Approved :: GNU General Public License (GPL)',
				'Natural Language :: English',
				'Operating System :: OS Independent',
				'Programming Language :: Python',
				'Programming Language :: Python :: 2',
				'Programming Language :: Python :: 2.5',
				'Topic :: System :: Systems Administration :: Authentication/Directory'
				]
)
