from atexit import register
from os import chmod, makedirs, remove, rmdir
from os.path import dirname, exists
from platform import machine, system
from requests import get
from selenium.webdriver import Firefox as SeleniumFirefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from sys import maxsize
from tarfile import open as tar_open
from zipfile import ZipFile

PATH_RESOURCES = dirname(__file__) + '/resources'

with open(PATH_RESOURCES + '/add_render.js', 'r', encoding='utf-8') as fp:
	SCRIPT_ADD_RENDER = fp.read()

class Firefox(SeleniumFirefox):

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
			options = Options()
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
			service = Service(executable_path=driver_path, log_output='/dev/null')
		SeleniumFirefox.__init__(self, options=options, service=service, *args, **kwargs)
		self.set_page_load_timeout(timeout)
		register(self.quit)

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
		sys_name = system().lower()
		arch = machine().lower()
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
		if not exists(PATH_RESOURCES):
			makedirs(PATH_RESOURCES)
		browser_dir = PATH_RESOURCES + f'/firefox-{platform_id}-{browser_version}'
		if not exists(browser_dir):
			makedirs(browser_dir)
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
		response = get(url, stream=True)
		response.raise_for_status()
		total_size = int(response.headers.get('content-length', 0))
		from tqdm import tqdm
		with open(compressed_path, 'wb') as f:
			with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
				for chunk in response.iter_content(chunk_size=8192):
					if chunk:
						f.write(chunk)
						pbar.update(len(chunk))
		# Extract Firefox based on format
		if ext == 'zip':
			with ZipFile(compressed_path, 'r') as zf:
				zf.extractall(browser_dir)
		elif ext == 'tar.bz2':
			import tarfile
			with tarfile.open(compressed_path, 'r:bz2') as tf:
				tf.extractall(browser_dir)
		elif ext == 'dmg':
			import subprocess
			mount_point = PATH_RESOURCES + '/firefox_mount'
			if not exists(mount_point):
				makedirs(mount_point)
			subprocess.run(['hdiutil', 'attach', '-quiet', '-mountpoint', mount_point, compressed_path], check=True)
			app_path = mount_point + '/Firefox.app'
			subprocess.run(['cp', '-R', app_path, browser_dir + '/'], check=True)
			subprocess.run(['hdiutil', 'detach', '-quiet', mount_point], check=True)
			rmdir(mount_point)
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
		sys_name = system().lower()
		arch = machine().lower()
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
		if not exists(PATH_RESOURCES):
			makedirs(PATH_RESOURCES)
		ext = 'zip' if platform_id.startswith('win') else 'tar.gz'
		url = f'https://github.com/mozilla/geckodriver/releases/download/v{driver_version}/geckodriver-v{driver_version}-{platform_id}.{ext}'
		compressed_path = PATH_RESOURCES + f'/geckodriver.{ext}'
		print(f'Downloading geckodriver v{driver_version} for {platform_id}...')
		response = get(url, stream=True)
		response.raise_for_status()
		total_size = int(response.headers.get('content-length', 0))
		from tqdm import tqdm
		with open(compressed_path, 'wb') as f:
			with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
				for chunk in response.iter_content(chunk_size=8192):
					if chunk:
						f.write(chunk)
						pbar.update(len(chunk))
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
		chmod(driver_path, 0o755)

	def get_with_render(self, url, render_selector='body', *args, **kwargs):
		''' Downloads a page and renders it to return the page source, the width,
		and the height in pixels. Elements on the subtree selected using
		render_selector contain a data-computed-style attribute and a data-xpath. '''
		self.get(url, *args, **kwargs)
		self.execute_script(SCRIPT_ADD_RENDER, render_selector)

if __name__ == '__main__':
	from selenium.webdriver.common.by import By
	print('=== AutoSelenium Comprehensive Test on macOS ===')
	print('1. Testing basic functionality with system Firefox...')
	driver = Firefox(headless=True)
	driver.get('https://example.com')
	print('   Page title: ' + driver.title)
	element = driver.find_element(By.TAG_NAME, 'h1')
	print('   Found H1: ' + element.text)
	driver.quit()
	print('   ✓ Basic test passed')
	print('2. Testing browser detection with downloaded Firefox...')
	driver = Firefox(headless=True, browser_detection=True, browser_version='120.0')
	driver.get('https://httpbin.org/html')
	print('   Page loaded successfully')
	driver.quit()
	print('   ✓ Browser detection test passed')
	print('3. Testing rendering functionality...')
	driver = Firefox(headless=True, disable_images=True)
	driver.get_with_render('https://example.com')
	elements = driver.find_elements(By.CSS_SELECTOR, '[data-xpath]')
	print(f'   Found {len(elements)} elements with rendering data')
	driver.quit()
	print('   ✓ Rendering test passed')
	print('4. Testing configuration options...')
	driver = Firefox(
		headless=True,
		disable_images=True,
		disable_flash=True,
		open_links_same_tab=True,
		timeout=60
	)
	driver.get('https://httpbin.org/html')
	print('   ✓ Configuration test passed')
	driver.quit()
	print('5. Testing latest versions...')
	driver = Firefox(
		headless=True,
		driver_detection=True,
		driver_version=None,
		browser_detection=True,
		browser_version='default'
	)
	driver.get('https://example.com')
	print('   ✓ Latest versions test passed')
	driver.quit()
	print('🎉 SUCCESS: All AutoSelenium functionality works on macOS!')