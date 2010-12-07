========================
TracGoogleAppsAuthPlugin
========================

Plugin for Trac which allows user authentication against hosted Google Apps account.

Features:

* Allows users to log in to Trac with their Google Apps username and password

* Allows restriction of userbase for Trac instance based on membership in Google Apps group

* Assigns Trac groups to users based on their Google Apps groups

* Allows basic user info listing via Trac Account Manager

* Pre-populates Trac database with email of every user so that email
  notifications can be sent to users who have never logged in to Trac, and so
  the ticket "Assign To" drop-down is fully populated when using the config
  `[ticket]` setting `restrict_owner = true`. Simply view the Admin user
  listing page to populate the database.
 
* Encrypts stored Google Apps password to protect against casual observers on
  filesystem and via web, but this is not nearly as secure as using OpenID

Please note that this software is currently in "alpha" state and under active development!

Author: David A. Riggs <david.riggs@createtank.com>


License
=======

Copyright 2010 createTank, LLC

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
Version 2 as published by the Free Software Foundation.

http://www.gnu.org/licenses/old-licenses/gpl-2.0.html


Requirements
============

This plugin requires:

* Trac (tested with 0.12)

* Google's `gdata <http://code.google.com/p/gdata-python-client/>`_

* Trac `AccountManagerPlugin <http://trac-hacks.org/wiki/AccountManagerPlugin>`_


``$> sudo easy_install gdata``

``$> sudo easy_install https://trac-hacks.org/svn/accountmanagerplugin/trunk``


Installation
============

To magically install from the PyPI,

``$> sudo easy_install TracGoogleAppsAuthPlugin``

... or from source,

``$> sudo python setup.py install``


Configuration
=============

Trac 'trac.ini' configuration::

	[account-manager]
	password_store = GoogleAppsPasswordStore
	
	[components]
	acct_mgr.api.accountmanager = enabled
	acct_mgr.web_ui.loginmodule = enabled
	googleappsauth.googleauthplugin.googleappspasswordstore = enabled
	trac.web.auth.loginmodule = disabled
	
	[google_apps]
	domain = mydomainname.com
	group_access = trac_users
	admin_username = sysadmin
	admin_secret = TOP_S3CRET

You can configure most (all?) of these settings from the Trac web-based Admin console. Essentially,
if you already have the web-based TracAccountManager plugin enabled and working, just enable the
GoogleAppsPasswordStore (under TracGoogleAppsAuthPlugin) and disable the other password stores
HtDigestStore and HtPasswdStore (under TracAccountManager). You can then configure the plugin
via the Accounts / Configuration menu of the Trac web-based Admin.

Detailed documentation TODO...
