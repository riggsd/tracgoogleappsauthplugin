"""
Google Apps authentication plugin for Trac
"""

from trac.core import *	#@UnusedWildImport
from trac.config import Option, BoolOption
from trac.env import ISystemInfoProvider
from trac.perm import IPermissionGroupProvider

from acct_mgr.api import IPasswordStore

from gdata.apps.service import AppsService
from gdata.apps.groups.service import GroupsService
from gdata.service import BadAuthentication, CaptchaRequired
from gdata.apps.service import AppsForYourDomainException

from base64 import b64encode, b64decode

# i18n
from pkg_resources import resource_filename	#@UnresolvedImport
from trac.util.translation import domain_functions
_, add_domain = domain_functions('googleappsauth', ('_', 'add_domain'))


class GoogleAppsPasswordStore(Component):
	"""TracAccountManager Password Store which authenticates against a Google Apps domain"""
	
	implements(IPasswordStore, IPermissionGroupProvider, ISystemInfoProvider)
	
	# Plugin Options
	opt_key = 'google_apps'
	
	gapps_domain = Option(opt_key, 'domain', doc=_("Domain name of the Google Apps domain"))
	gapps_admin_username = Option(opt_key, 'admin_username', doc=_("Username or email with Google Apps admin access"))
	gapps_admin_secret = Option(opt_key, 'admin_secret', doc=_("Password for Google Apps admin account; this is magically encrypted to make storage slightly more secure"))
	gapps_group_access = Option(opt_key, 'group_access', doc=_("Optional Google Apps Group which is exclusively granted access to this Trac site"))
	#enable_multiple_stores = BoolOption(opt_key, 'enable_multiple_stores', False, """Optional flag to enable use of this plugin alongside other PasswordStore implementations (will slightly increase network overhead)""")
	
	
	def __init__(self):
		self.env.log.debug('GoogleAppsPasswordStore.__init__()')
		self.env.log.debug('domain: %s\tadmin_username: %s\tadmin_secret: %s\tgroup_access: %s' % \
						(self.gapps_domain, self.gapps_admin_username, len(self.gapps_admin_secret)*'*', self.gapps_group_access))

		self.group_cache = {'anonymous':[],}
		
		if not self._is_encrypted(self.gapps_admin_secret):
			self.env.log.debug('Attempting to encrypt config option "[google_apps] admin_secret" ...')
			try:
				self.config.set(self.opt_key, 'admin_secret', self._encrypt(self.gapps_admin_secret))
				self.config.save()
			except OSError, e:
				self.env.log.debug(e)
		
		# i18n
		locale_dir = resource_filename(__name__, 'locale')
		add_domain(self.env.path, locale_dir)
	
	def _validate(self):
		"""Validate that the plugin is configured correctly"""
		return self.gapps_domain and self.gapps_admin_username and self.gapps_admin_secret
	
	def _is_encrypted(self, val):
		return val and val.startswith('{enc}')
		
	def _decrypt(self, val):
		if self._is_encrypted(val):
			encrypted_str = val.split('{enc}',1)[1]
			decrypted_str = b64decode(encrypted_str)
			return decrypted_str
		else:
			return val
	
	def _encrypt(self, val):
		if self._is_encrypted(val):
			return val
		else:
			return '{enc}'+b64encode(val)
	
	def _get_user_email(self, username):
		if username.find('@') > -1:
			email = username
		else:
			email = '%s@%s' % (username, self.gapps_domain)
		return email

	def _get_admin_email(self):
		return self._get_user_email(self.gapps_admin_username)
	
	def _get_apps_service(self):
		"""Build instance of gdata AppsService ready for ProgrammaticLogin()"""
		email = self._get_admin_email()
		password = self._decrypt(self.gapps_admin_secret)
		return AppsService(email=email, domain=self.gapps_domain, password=password)
	
	def _get_groups_service(self):
		"""Build instance of gdata GroupsService ready for ProgrammaticLogin()"""
		email = self._get_admin_email()
		password = self._decrypt(self.gapps_admin_secret)
		return GroupsService(email=email, domain=self.gapps_domain, password=password)
	
	def _populate_user_metadata(self, username, email, name=None):
		"""Populate a user's metadata in the Trac DB so they appear in dropdown
		lists and so email is available to notification subsystem"""
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		# WARNING: SQL only tested with sqlite3; make this PostgreSQL friendly
		# by only INSERTing for sid's which don't exist already (which is also
		# an optimization, as single SELECT is probably faster than multiple
		# INSERT IGNOREs)
		cursor.execute('INSERT OR IGNORE INTO session (sid, authenticated, last_visit) VALUES (%s, 1, 0)', (username,))
		cursor.execute('INSERT OR IGNORE INTO session_attribute (sid, authenticated, name, value) VALUES (%s, 1, "email", %s)', (username, email))
		if name:
			cursor.execute('INSERT OR IGNORE INTO session_attribute (sid, authenticated, name, value) VALUES (%s, 1, "name", %s)', (username, name))
		db.commit()
	
	def _populate_users_metadata_all(self, gapps_users_feed):
		"""_populate_user_metadata with AppsService users feed"""
		self.log.debug('Populating Trac DB user metadata ...')
		for user in gapps_users_feed.entry:
			username = user.login.user_name
			name = '%s %s'%(user.name.given_name, user.name.family_name)
			email = self._get_user_email(user.login.user_name)
			self._populate_user_metadata(username, email, name)
	
	def _populate_users_metadata_in_group(self, user_list):
		"""_populate_user_metadata with only a username list"""
		self.log.debug('Populating Trac DB user metadata ...')
		for username in user_list:
			email = self._get_user_email(username)
			self._populate_user_metadata(username, email)
	
	def _get_all_users(self):
		"""Retrieve list of all usernames from Google Apps"""
		service = self._get_apps_service()
		service.ProgrammaticLogin()
		gapps_users_feed = service.RetrieveAllUsers()
		#self.log.debug(gapps_users_feed)  # DEBUG
		users = [user.login.user_name for user in gapps_users_feed.entry]
		self._populate_users_metadata_all(gapps_users_feed)  # EXPERIMENTAL!
		return users
		
	def _get_all_users_in_group(self, group, suspended_users=True):
		"""Retrieve list of all usernames belonging to specified group from Google Apps"""
		service = self._get_groups_service()
		service.ProgrammaticLogin()
		gapps_users_feed = service.RetrieveAllMembers(group, suspended_users)  # BUG catch AppsForYourDomainException if group doesn't exist
		#self.log.debug(gapps_users_feed)  # DEBUG
		emails = [user_dict['memberId'] for user_dict in gapps_users_feed]  # Groups service gives us email addresses instead of usernames
		users = [email.split('@')[0] for email in emails if email.endswith(self.gapps_domain)]  # toss out members outside our domain
		self._populate_users_metadata_in_group(users)  # EXPERIMENTAL!
		return users
	
	def _user_in_group(self, username, groupname):
		"""Is user a member of specified group?"""
		groups_service = self._get_groups_service()
		groups_service.ProgrammaticLogin()
		return groups_service.IsMember(username, groupname)

	
	# IPasswordStore API
	
	def get_users(self):
		"""Returns an iterable of the known usernames."""
		self.log.debug('get_users')
		if not self._validate():
			self.log.debug('Plugin validation failed (check config!), falling through.')
			return []
		
		if self.gapps_group_access:
			self.log.debug('Restricting user list to members of group "%s".' % (self.gapps_group_access))
			return self._get_all_users_in_group(self.gapps_group_access)
		else:
			return self._get_all_users()

	def has_user(self, user):
		"""Returns whether the user account exists."""
		self.log.debug('has_user(%s)' % (user))
		return user in self.get_users()

	def has_email(self, address):
		"""Returns whether a user account with that email address exists."""
		self.log.debug('has_email(%s)' % (address))
		user = address.split('@')[0]
		return user in self.get_users() 

	def set_password(self, user, password, old_password=None):
		"""Sets the password for the user.  This should create the user account
		if it doesn't already exist.
		Returns True if a new account was created, False if an existing account
		was updated.
		"""
		self.log.debug('set_password(%s): NOT IMPLEMENTED' % (user))
		return None # TODO

	def check_password(self, user, password):
		"""Checks if the password is valid for the user.
	
		Returns True if the correct user and password are specfied.  Returns
		False if the incorrect password was specified.  Returns None if the
		user doesn't exist in this password store.

		Note: Returing `False` is an active rejection of the login attempt.
		Return None to let the auth fall through to the next store in the
		chain.
		"""
		self.log.debug('check_password(%s, %s)' % (user, len(password)*'*'))
		if not self._validate():
			self.log.debug('Plugin validation failed (check config!), falling through.')
			return None
		
		if user.find('@') > -1:
			self.log.debug('User entered email instead of username, falling through.')
			return None
		
		# This should allow the use of multiple PasswordStore implementations at the expense of making the login process slower...
		#if self.enable_multiple_stores and user not in self.get_users():
		#	self.log.debug('User "%s" is not one of our users, Google Apps plugin falling through.' % (user))
		#	return None
		
		email = self._get_user_email(user)		
		service = self._get_apps_service()
		try:
			service.ClientLogin(email, password, account_type='HOSTED', source='createtank-tracgoogleappsauthplugin-0.3')
			
			if self.gapps_group_access and not self._user_in_group(user, self.gapps_group_access):
				self.log.debug('User "%s" not in required Google Apps group "%s", login rejected.' % (user, self.gapps_group_access))
				return False
			
			if self.group_cache.has_key(user):
				self.log.debug('Flushing group cache for user "%s".' % (user))
				del self.group_cache[user]
			return True
		except BadAuthentication, e:
			self.log.debug(e)
			return False
		except CaptchaRequired, e:
			self.log.debug(e) # yikes?!
			return False
		
		return None # ?

	def delete_user(self, user):
		"""Deletes the user account.
		Returns True if the account existed and was deleted, False otherwise.
		"""
		self.log.debug('delete_user(%s): NOT IMPLEMENTED' % (user))
		return False

	def config_key(self):
		"""'''Deprecated'''
		Returns a string used to identify this implementation in the config.
		This password storage implementation will be used if the value of
		the config property "account-manager.password_format" matches.
		This implementation uses the key 'googleappsauth'.
		"""
		return 'googleappsauth'


	# IPermissionGroupProvider API

	def get_permission_groups(self, username):
		"""Return a list of names of the groups that the user with the specified name is a member of."""
		self.log.debug('get_permission_groups(%s)' % (username))
		
		if username == 'anonymous':
			self.log.debug('This plugin does not authenticate anonymous user.')
			return []
		
		if not self._validate():
			self.log.debug('Plugin validation failed (check config!), falling through.')
			return []

		
		groups = []
		if self.group_cache.has_key(username):
			self.log.debug('returning cached groups for user: '+username)
			groups = self.group_cache[username]
		else:
			self.log.debug('groups not cached, requesting from Google Apps for user: '+username)
			service = self._get_groups_service()
			try:
				service.ProgrammaticLogin()  # BUG blows up with CaptchaRequired under heavy load
				groups_feed = service.RetrieveGroups(username, False)
				groups = [group_dict['groupName'] for group_dict in groups_feed]
		
				self.group_cache[username] = groups
			except AppsForYourDomainException, e:
				self.log.debug(e)
				self.log.debug('Failed to retrieve groups for user "%s", caching [] to avoid problems!')
				groups = []
				self.group_cache[username] = groups
			
		#self.log.debug(groups)
		return groups
	
	
	# ISystemInfoProvider API
	
	def get_system_info(self):
		"""Yield a sequence of `(name, version)` tuples describing the name and
		version information of external packages used by a component.
		"""
		import gdata
		from trac.util import get_pkginfo
		yield 'Google Data', get_pkginfo(gdata)['version']
