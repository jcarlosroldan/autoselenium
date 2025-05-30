from atexit import register
from os import chmod, makedirs, remove, rmdir
from os.path import dirname, exists
from platform import machine, system
from requests import get
from selenium.webdriver import Chrome as SeleniumChrome
from selenium.webdriver import Firefox as SeleniumFirefox
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from sys import maxsize
from tarfile import open as tar_open
from zipfile import ZipFile

PATH_RESOURCES = dirname(__file__) + '/resources'

with open(PATH_RESOURCES + '/add_render.js', 'r', encoding='utf-8') as fp:
	SCRIPT_ADD_RENDER = fp.read()

class AutoBrowser:
	def _setup_common(self, timeout):
		''' Sets up common browser configuration. '''
		self.set_page_load_timeout(timeout)
		register(self.quit)
	def get_with_render(self, url, render_selector='body', *args, **kwargs):
		''' Downloads a page and renders it to return the page source, the width,
		and the height in pixels. Elements on the subtree selected using
		render_selector contain a data-computed-style attribute and a data-xpath. '''
		self.get(url, *args, **kwargs)
		self.execute_script(SCRIPT_ADD_RENDER, render_selector)

class Chrome(AutoBrowser, SeleniumChrome):
	def __init__(
		self,
		browser_detection=False,
		browser_version='default',
		driver_detection=True,
		driver_version=None,
		headless=False,
		disable_images=True,
		disable_flash=True,
		timeout=30,
		options=None,
		*args,
		**kwargs
	):
		''' Returns a Chrome webdriver with customised configuration. '''
		if options is None:
			options = ChromeOptions()
		if headless:
			options.add_argument('--headless')
		if disable_images:
			options.add_experimental_option('prefs', {'profile.managed_default_content_settings.images': 2})
		if disable_flash:
			options.add_argument('--disable-plugins')
		# Browser setup
		if browser_detection:
			if browser_version == 'default':
				browser_version = self._get_latest_chrome_version()
			browser_path = self.detect_browser(browser_version)
			options.binary_location = browser_path
		# Service setup
		service = None
		if driver_detection:
			driver_path = self._get_driver(driver_version)
			service = ChromeService(executable_path=driver_path, log_output='/dev/null')
		SeleniumChrome.__init__(self, options=options, service=service, *args, **kwargs)
		self._setup_common(timeout)

	def detect_browser(self, browser_version):
		''' Detects and downloads Chrome browser for the current platform. '''
		platform_id = self._get_browser_platform()
		browser_dir = PATH_RESOURCES + f'/chrome-{platform_id}-{browser_version}'
		if platform_id.startswith('win'):
			browser_path = browser_dir + '/chrome.exe'
		elif platform_id == 'mac':
			browser_path = browser_dir + '/Google Chrome.app/Contents/MacOS/Google Chrome'
		else:
			browser_path = browser_dir + '/chrome'
		if not exists(browser_path):
			self._download_browser(platform_id, browser_version)
		return browser_path

	def _get_latest_chrome_version(self):
		''' Gets the latest Chrome version from Google API. '''
		response = get('https://chromiumdash.appspot.com/fetch_releases?channel=Stable&platform=Windows&num=1')
		response.raise_for_status()
		return response.json()[0]['version']

	def _get_browser_platform(self):
		''' Returns the platform identifier for Chrome downloads. '''
		sys_name, arch = _get_system_info()
		if sys_name == 'linux':
			if arch in ['x86_64', 'amd64']:
				return 'linux64'
			else:
				return 'linux32'
		elif sys_name == 'darwin':
			if arch in ['arm64', 'aarch64']:
				return 'mac-arm64'
			else:
				return 'mac-x64'
		elif sys_name == 'windows':
			if arch in ['x86_64', 'amd64']:
				return 'win64'
			else:
				return 'win32'
		else:
			raise RuntimeError(f'Unsupported platform for Chrome: {sys_name}/{arch}')

	def _download_browser(self, platform_id, browser_version):
		''' Downloads and extracts Chrome for the given platform. '''
		_ensure_dir(PATH_RESOURCES)
		browser_dir = PATH_RESOURCES + f'/chrome-{platform_id}-{browser_version}'
		_ensure_dir(browser_dir)
		# Chrome download URLs
		base_url = 'https://dl.google.com/chrome/install/'
		if platform_id == 'win64':
			url = base_url + 'GoogleChromeStandaloneEnterprise64.msi'
			ext = 'msi'
		elif platform_id == 'win32':
			url = base_url + 'GoogleChromeStandaloneEnterprise.msi'
			ext = 'msi'
		elif platform_id in ['mac-x64', 'mac-arm64']:
			url = base_url + 'googlechrome.dmg'
			ext = 'dmg'
		else:
			url = f'https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_{browser_version}-1_amd64.deb'
			ext = 'deb'
		compressed_path = PATH_RESOURCES + f'/chrome-{browser_version}.{ext}'
		print(f'Downloading Chrome v{browser_version} for {platform_id}...')
		_download_with_progress(url, compressed_path)
		# Extract Chrome based on format
		if ext in ['msi', 'deb']:
			raise RuntimeError(f'Chrome installer extraction not yet implemented for {platform_id}. Please install Chrome manually.')
		elif ext == 'dmg':
			_extract_dmg(compressed_path, browser_dir, 'Google Chrome.app')
		remove(compressed_path)

	def _get_driver(self, driver_version):
		''' Downloads and returns the chromedriver path for the current platform. '''
		if driver_version is None:
			driver_version = self._get_compatible_driver_version()
		platform_id = self._get_driver_platform()
		driver_path = PATH_RESOURCES + f'/chromedriver-{platform_id}-{driver_version}'
		if not exists(driver_path):
			self._download_driver(platform_id, driver_path, driver_version)
		return driver_path

	def _get_compatible_driver_version(self):
		''' Gets the chromedriver version compatible with installed Chrome. '''
		chrome_version = self._get_installed_chrome_version()
		if chrome_version:
			print(f'   Detected Chrome version: {chrome_version}')
			# Get major version (e.g., "136" from "136.0.7103.116")
			major_version = chrome_version.split('.')[0]
			try:
				# Try to get compatible driver version for this Chrome version
				response = get(f'https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_{major_version}')
				if response.status_code == 200:
					compatible_version = response.text.strip()
					print(f'   Using compatible chromedriver: {compatible_version}')
					return compatible_version
			except:
				pass
		# Fallback to latest stable if we can't determine compatibility
		print('   Could not detect Chrome version, using latest chromedriver')
		return self._get_latest_driver_version()

	def _get_installed_chrome_version(self):
		''' Gets the version of installed Chrome browser. '''
		import subprocess
		sys_name, _ = _get_system_info()
		try:
			if sys_name == 'darwin':
				result = subprocess.run(
					['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
					capture_output=True, text=True, timeout=5
				)
			elif sys_name == 'linux':
				result = subprocess.run(
					['google-chrome', '--version'],
					capture_output=True, text=True, timeout=5
				)
			elif sys_name == 'windows':
				try:
					import winreg
					key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
					version, _ = winreg.QueryValueEx(key, 'version')
					return version
				except ImportError:
					return None
			else:
				return None
			if result.returncode == 0:
				# Extract version from output like "Google Chrome 136.0.7103.116"
				version_line = result.stdout.strip()
				version = version_line.split()[-1]
				return version
		except:
			pass
		return None

	def _get_latest_driver_version(self):
		''' Gets the latest chromedriver version from Google API. '''
		response = get('https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE')
		response.raise_for_status()
		return response.text.strip()

	def _get_driver_platform(self):
		''' Returns the platform identifier for chromedriver downloads. '''
		sys_name, arch = _get_system_info()
		if sys_name == 'linux':
			return 'linux64'
		elif sys_name == 'darwin':
			if arch in ['arm64', 'aarch64']:
				return 'mac-arm64'
			else:
				return 'mac-x64'
		elif sys_name == 'windows':
			if arch in ['x86_64', 'amd64']:
				return 'win64'
			else:
				return 'win32'
		else:
			raise RuntimeError(f'Unsupported platform: {sys_name}/{arch}')

	def _download_driver(self, platform_id, driver_path, driver_version):
		''' Downloads and extracts chromedriver for the given platform. '''
		_ensure_dir(PATH_RESOURCES)
		url = f'https://storage.googleapis.com/chrome-for-testing-public/{driver_version}/{platform_id}/chromedriver-{platform_id}.zip'
		compressed_path = PATH_RESOURCES + '/chromedriver.zip'
		print(f'Downloading chromedriver v{driver_version} for {platform_id}...')
		_download_with_progress(url, compressed_path)
		# Extract driver
		with ZipFile(compressed_path, 'r') as zf:
			driver_name = 'chromedriver.exe' if platform_id.startswith('win') else 'chromedriver'
			with open(driver_path, 'wb') as f:
				f.write(zf.read(f'chromedriver-{platform_id}/{driver_name}'))
		remove(compressed_path)
		_make_executable(driver_path)

class Firefox(AutoBrowser, SeleniumFirefox):
	def __init__(
		self,
		browser_detection=False,
		browser_version='default',
		driver_detection=True,
		driver_version=None,
		headless=False,
		disable_images=True,
		disable_flash=True,
		open_links_same_tab=False,
		timeout=30,
		options=None,
		*args,
		**kwargs
	):
		''' Returns a Firefox webdriver with customised configuration. '''
		if options is None:
			options = FirefoxOptions()
		if headless:
			options.add_argument('--headless')
		if disable_images:
			options.set_preference('permissions.default.image', 2)
		if disable_flash:
			options.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
		if open_links_same_tab:
			options.set_preference('browser.link.open_newwindow.restriction', 0)
			options.set_preference('browser.link.open_newwindow', 1)
		# Browser setup
		if browser_detection:
			if browser_version == 'default':
				browser_version = self._get_latest_firefox_version()
			browser_path = self.detect_browser(browser_version)
			options.binary_location = browser_path
		# Service setup
		service = None
		if driver_detection:
			driver_path = self._get_driver(driver_version)
			service = FirefoxService(executable_path=driver_path, log_output='/dev/null')
		SeleniumFirefox.__init__(self, options=options, service=service, *args, **kwargs)
		self._setup_common(timeout)

	def detect_browser(self, browser_version):
		''' Detects and downloads Firefox browser for the current platform. '''
		platform_id = self._get_browser_platform()
		browser_dir = PATH_RESOURCES + f'/firefox-{platform_id}-{browser_version}'
		if platform_id.startswith('win'):
			browser_path = browser_dir + '/firefox/firefox.exe'
		elif platform_id == 'mac':
			browser_path = browser_dir + '/Firefox.app/Contents/MacOS/firefox'
		else:
			browser_path = browser_dir + '/firefox/firefox'
		if not exists(browser_path):
			self._download_browser(platform_id, browser_version)
		return browser_path

	def _get_latest_firefox_version(self):
		''' Gets the latest Firefox version from Mozilla API. '''
		response = get('https://product-details.mozilla.org/1.0/firefox_versions.json')
		response.raise_for_status()
		return response.json()['LATEST_FIREFOX_VERSION']

	def _get_browser_platform(self):
		''' Returns the platform identifier for Firefox downloads. '''
		sys_name, arch = _get_system_info()
		if sys_name == 'linux':
			if arch in ['x86_64', 'amd64']:
				return 'linux-x86_64'
			else:
				return 'linux-i686'
		elif sys_name == 'darwin':
			return 'mac'
		elif sys_name == 'windows':
			if arch in ['x86_64', 'amd64']:
				return 'win64'
			else:
				return 'win32'
		else:
			raise RuntimeError(f'Unsupported platform for Firefox: {sys_name}/{arch}')

	def _download_browser(self, platform_id, browser_version):
		''' Downloads and extracts Firefox for the given platform. '''
		_ensure_dir(PATH_RESOURCES)
		browser_dir = PATH_RESOURCES + f'/firefox-{platform_id}-{browser_version}'
		_ensure_dir(browser_dir)
		# Build URL and extension based on platform
		base_url = f'https://archive.mozilla.org/pub/firefox/releases/{browser_version}/'
		if platform_id in ['win64', 'win32']:
			url = base_url + f'{platform_id}/en-US/firefox-{browser_version}.zip'
			ext = 'zip'
		elif platform_id == 'mac':
			url = base_url + f'mac/en-US/Firefox%20{browser_version}.dmg'
			ext = 'dmg'
		else:
			url = base_url + f'{platform_id}/en-US/firefox-{browser_version}.tar.bz2'
			ext = 'tar.bz2'
		compressed_path = PATH_RESOURCES + f'/firefox-{browser_version}.{ext}'
		print(f'Downloading Firefox v{browser_version} for {platform_id}...')
		_download_with_progress(url, compressed_path)
		# Extract Firefox based on format
		if ext == 'zip':
			with ZipFile(compressed_path, 'r') as zf:
				zf.extractall(browser_dir)
		elif ext == 'tar.bz2':
			import tarfile
			with tarfile.open(compressed_path, 'r:bz2') as tf:
				tf.extractall(browser_dir)
		elif ext == 'dmg':
			_extract_dmg(compressed_path, browser_dir, 'Firefox.app')
		remove(compressed_path)

	def _get_driver(self, driver_version):
		''' Downloads and returns the geckodriver path for the current platform. '''
		if driver_version is None:
			driver_version = self._get_latest_driver_version()
		platform_id = self._get_driver_platform()
		driver_path = PATH_RESOURCES + f'/geckodriver-{platform_id}-{driver_version}'
		if not exists(driver_path):
			self._download_driver(platform_id, driver_path, driver_version)
		return driver_path

	def _get_latest_driver_version(self):
		''' Gets the latest geckodriver version from GitHub API. '''
		response = get('https://api.github.com/repos/mozilla/geckodriver/releases/latest')
		response.raise_for_status()
		return response.json()['tag_name'].lstrip('v')

	def _get_driver_platform(self):
		''' Returns the platform identifier for geckodriver downloads. '''
		sys_name, arch = _get_system_info()
		if sys_name == 'linux':
			if arch in ['aarch64', 'arm64']:
				return 'linux-aarch64'
			elif arch in ['x86_64', 'amd64']:
				return 'linux64'
			else:
				return 'linux32'
		elif sys_name == 'darwin':
			if arch in ['arm64', 'aarch64']:
				return 'macos-aarch64'
			else:
				return 'macos'
		elif sys_name == 'windows':
			if arch in ['aarch64', 'arm64']:
				return 'win-aarch64'
			else:
				bits = 64 if maxsize > 2**32 else 32
				return f'win{bits}'
		else:
			raise RuntimeError(f'Unsupported platform: {sys_name}/{arch}')

	def _download_driver(self, platform_id, driver_path, driver_version):
		''' Downloads and extracts geckodriver for the given platform. '''
		_ensure_dir(PATH_RESOURCES)
		ext = 'zip' if platform_id.startswith('win') else 'tar.gz'
		url = f'https://github.com/mozilla/geckodriver/releases/download/v{driver_version}/geckodriver-v{driver_version}-{platform_id}.{ext}'
		compressed_path = PATH_RESOURCES + f'/geckodriver.{ext}'
		print(f'Downloading geckodriver v{driver_version} for {platform_id}...')
		_download_with_progress(url, compressed_path)
		# Extract driver
		if ext == 'zip':
			with ZipFile(compressed_path, 'r') as zf:
				with open(driver_path, 'wb') as f:
					f.write(zf.read('geckodriver.exe' if platform_id.startswith('win') else 'geckodriver'))
		else:
			with tar_open(compressed_path, 'r:gz') as tf:
				with tf.extractfile('geckodriver') as gd:
					with open(driver_path, 'wb') as f:
						f.write(gd.read())
		remove(compressed_path)
		_make_executable(driver_path)

def _download_with_progress(url, path):
	''' Downloads a file with progress bar. '''
	response = get(url, stream=True)
	response.raise_for_status()
	total_size = int(response.headers.get('content-length', 0))
	from tqdm import tqdm
	with open(path, 'wb') as f:
		with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
			for chunk in response.iter_content(chunk_size=8192):
				if chunk:
					f.write(chunk)
					pbar.update(len(chunk))

def _extract_dmg(compressed_path, browser_dir, app_name):
	''' Extracts a DMG file on macOS. '''
	import subprocess
	mount_point = PATH_RESOURCES + '/temp_mount'
	_ensure_dir(mount_point)
	subprocess.run(['hdiutil', 'attach', '-quiet', '-mountpoint', mount_point, compressed_path], check=True)
	app_path = mount_point + '/' + app_name
	subprocess.run(['cp', '-R', app_path, browser_dir + '/'], check=True)
	subprocess.run(['hdiutil', 'detach', '-quiet', mount_point], check=True)
	rmdir(mount_point)

def _ensure_dir(path):
	''' Creates directory if it doesn't exist. '''
	if not exists(path):
		makedirs(path)

def _make_executable(path):
	''' Makes file executable. '''
	chmod(path, 0o755)

def _get_system_info():
	''' Returns system name and architecture. '''
	return system().lower(), machine().lower()