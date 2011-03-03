#!/usr/bin/env python

from setuptools import find_packages, setup

extra = {}

try:
	from trac.util.dist  import  get_l10n_cmdclass
	cmdclass = get_l10n_cmdclass()
	if cmdclass:
		extra['cmdclass'] = cmdclass
		extractors = [
			('**.py',				'python', None),
			('**/templates/**.html', 'genshi', None),
		]
		extra['message_extractors'] = {
			'googleappsauth': extractors,
		}
# i18n is implemented to be optional here
except ImportError:
	pass


setup(
	name='TracGoogleAppsAuthPlugin',
	version='0.3.1',
	author='David A. Riggs',
	author_email='david.riggs@createtank.com',
	url='http://code.google.com/p/tracgoogleappsauthplugin/',
	download_url='http://code.google.com/p/tracgoogleappsauthplugin/',
	description='Trac authentication plugin for integration with hosted Google Apps domain',
	long_description=open('README.txt').read(),
	install_requires = ['Trac >= 0.12', 'gdata >= 2.0.0'],
	packages=['googleappsauth'],
	package_data = {
				'googleappsauth': [
								'locale/*.pot',
								'locale/*/LC_MESSAGES/*.mo',
								]
				},
	entry_points = '''
		[trac.plugins]
		googleappsauth = googleappsauth
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
				],
	**extra
)
