from atexit import register
from datetime import timedelta
from os import remove, chmod
from os.path import join, dirname, exists
from re import findall
from requests import get
from selenium.webdriver import Firefox as SeleniumFirefox
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options
from sys import platform, maxsize, stdout
from time import time
from urllib.request import urljoin

PATH_RESOURCES = join(dirname(__file__), 'resources')

with open(join(PATH_RESOURCES, 'add_render.js'), 'r', encoding='utf-8') as fp:
	SCRIPT_ADD_RENDER = fp.read()

class Firefox(SeleniumFirefox):
	URL_DRIVER = 'https://github.com/mozilla/geckodriver/releases/tag/v%s'
	URL_BROWSER = 'http://ftp.mozilla.org/pub/firefox/releases/%s/'
	VERSION_DRIVER = '0.31.0'
	VERSION_BROWSER = '100.0b9'  # from https://firefox-source-docs.mozilla.org/testing/geckodriver/Support.html
	REGEX_LINK = 'href="(/mozilla/geckodriver/releases/download/.+?%s.+?)"'

	def __init__(
		self,
		browser_detection='default', browser_version='default',
		driver_detection=True, driver_version='default',
		headless=False,
		disable_images=True,
		open_links_same_tab=False, disable_flash=True,
		timeout=15,
		options=None,
		*args, **kwargs
	):
		''' Returns a Firefox webdriver with customised configuration. '''
		if options is None:
			options = Options()
		if disable_flash:
			options.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
		if open_links_same_tab:
			options.set_preference('browser.link.open_newwindow.restriction', 0)
			options.set_preference('browser.link.open_newwindow', 1)
		if headless:
			options.headless = True
		if disable_images:
			options.set_preference('permissions.default.image', 2)
		if browser_detection:
			if browser_version == 'default':
				browser_version = Firefox.VERSION_BROWSER
			else:
				kwargs['firefox_binary'] = FirefoxBinary(self.detect_browser())
		if driver_detection:
			if driver_version == 'default':
				driver_version = Firefox.VERSION_DRIVER
			kwargs['executable_path'], kwargs['service_log_path'] = self.detect_driver(driver_version)
		SeleniumFirefox.__init__(self, options=options, *args, **kwargs)
		self.set_page_load_timeout(timeout)
		register(self.quit)

	def detect_browser(self, browser_version):
		pass

	def detect_driver(self, driver_version):
		null_path = '/dev/null'
		bits = 64 if maxsize > 2**32 else 32
		if platform.startswith('linux'):
			identifier = 'linux%s' % bits
		elif platform == 'win32':
			identifier = 'win%s' % bits
			null_path = 'NUL'
		elif platform == 'darwin':
			identifier = 'macos'
		else:
			raise RuntimeError('Platform %s not recognised. Please install geckodriver manually, add it to the PATH, and set the detect_driver_path to False.' % platform)
		driver_path = join(PATH_RESOURCES, 'geckodriver-%s' % identifier)
		if not exists(driver_path):
			url = Firefox.URL_DRIVER % driver_version
			page = get(url).text
			url_driver = urljoin(url, findall(Firefox.REGEX_LINK % identifier, page)[0])
			compressed_path = join(PATH_RESOURCES, url_driver.rsplit('/', 1)[1])
			download_file(url_driver, compressed_path)
			if compressed_path.endswith('.zip'):
				from zipfile import ZipFile
				with ZipFile(compressed_path, 'r') as zf:
					with open(driver_path, 'wb') as f:
						f.write(zf.read(zf.namelist()[0]))
			else:
				from tarfile import open as tar_open
				with tar_open(compressed_path, 'r:gz') as tf:
					with tf.extractfile('geckodriver') as gd, open(driver_path, 'wb') as f:
						f.write(gd.read())
			remove(compressed_path)
			chmod(driver_path, 755)
		return driver_path, null_path

	def get_with_render(self, url, render_selector='body', *args, **kwargs):
		''' Downloads a page and renders it to return the page source, the width,
		and the height in pixels. Elements on the subtree selected using
		render_selector contain a data-computed-style attribute and a data-xpath. '''
		self.get(url, *args, **kwargs)
		self.execute_script(SCRIPT_ADD_RENDER, render_selector)

# --- auxiliar ----------------------------------------------------------------

def download_file(url, path=None, chunk_size=10**5):
	''' Downloads a file keeping track of the progress. '''
	if path is None:
		path = url.split('/')[-1]
	r = get(url, stream=True)
	total_bytes = int(r.headers.get('content-length'))
	bytes_downloaded = 0
	start = time()
	print('Downloading %s (%s)' % (url, bytes_to_human(total_bytes)))
	with open(path, 'wb') as fp:
		for chunk in r.iter_content(chunk_size=chunk_size):
			if chunk:
				fp.write(chunk)
				bytes_downloaded += len(chunk)
				percent = bytes_downloaded / total_bytes
				bar = ('█' * int(percent * 32)).ljust(32)
				time_delta = time() - start
				eta = seconds_to_human((total_bytes - bytes_downloaded) * time_delta / bytes_downloaded)
				avg_speed = bytes_to_human(bytes_downloaded / time_delta).rjust(9)
				stdout.flush()
				stdout.write('\r  %6.02f%% |%s| %s/s eta %s' % (100 * percent, bar, avg_speed, eta))
	print()

def bytes_to_human(size, decimal_places=2):
	''' Returns a human readable file size from a number of bytes. '''
	unit = 0
	while size > 1024:
		size /= 1024
		unit += 1
	return '%.*f%sB' % (decimal_places, size, ' kMGTPEZY'[unit])

def seconds_to_human(seconds):
	''' Returns a human readable string from a number of seconds. '''
	return str(timedelta(seconds=int(seconds))).zfill(8)