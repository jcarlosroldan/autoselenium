from atexit import register
from datetime import timedelta
from glob import glob
from os import chmod, mkdir, remove, rmdir, rename
from os.path import basename, dirname, exists, join
from re import DOTALL, findall
from requests import get
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver import Firefox as SeleniumFirefox
from selenium.webdriver.firefox.options import Options
from shutil import copyfileobj, move
from subprocess import run
from sys import maxsize, platform, stdout
from time import time
from urllib.request import urljoin

PATH_RESOURCES = join(dirname(__file__), 'resources')

with open(join(PATH_RESOURCES, 'add_render.js'), 'r', encoding='utf-8') as fp:
    SCRIPT_ADD_RENDER = fp.read()


class Firefox(SeleniumFirefox):
    URL_DRIVER = 'https://github.com/mozilla/geckodriver/releases/tag/v%s'
    URL_RELEASES = 'https://ftp.mozilla.org/pub/firefox/releases/%s'
    URL_TABLE = 'https://firefox-source-docs.mozilla.org/testing/geckodriver/Support.html'
    VERSION_DRIVER = '0.26.0'
    REGEX_LINK = 'href="(/mozilla/geckodriver/releases/download/.+?%s.+?)"'

    def __init__(self, headless=False, disable_images=True, open_links_same_tab=False, disable_flash=True, detect_driver_path=True, timeout=15, driver_version='default', options=None, *args, **kwargs):
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
        if driver_version == 'default':
            driver_version = Firefox.VERSION_DRIVER
        if detect_driver_path:
            exec_path, log_path = self.find_driver_path(driver_version)
            if exec_path is None:
                raise RuntimeError('Platform %s not recognised. Please install geckodriver manually, add it to the PATH, and set the detect_driver_path to False.' % platform)
            try:
                SeleniumFirefox.__init__(self, options=options, executable_path=exec_path, service_log_path=log_path, *args, **kwargs)
            except SessionNotCreatedException:
                client_path = join(PATH_RESOURCES, 'firefox', driver_version)
                if not exists(client_path):
                    exec_path = self.download_firefox(driver_version)
                SeleniumFirefox.__init__(self, options=options, firefox_binary=exec_path, executable_path=exec_path, service_log_path=log_path, *args, **kwargs)
        else:
            SeleniumFirefox.__init__(self, options=options, *args, **kwargs)
        self.set_page_load_timeout(timeout)
        register(self.quit)

    def find_driver_path(self, driver_version):
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
            return None, None
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

    def download_firefox(self, driver_version, locale='en-US'):
        ''' Downloads the Firefox client and installs it at a folder named after
        the gecko version using a compatibility table.
        Also returns the path of the newly installed firefox executable. '''
        document = get(Firefox.URL_RELEASES % '')
        repo = findall(r'href=".+?/releases/([0-9.]+?)esr/?"', document.text)
        document = get(Firefox.URL_TABLE)
        versions = findall(r'<tr>\s*<td>(.+?)\s*<td>.+?<td>(.+?)\s*<td>(.+?)\s', document.text, flags=DOTALL)
        versions = {
            version: {'min': min_ver, 'max': max_ver if max_ver != 'n/a' else repo[-1]}
            for version, min_ver, max_ver in versions
        }
        if driver_version in versions:
            if versions[driver_version]['max'] in repo:
                version = versions[driver_version]['max']
            else:
                candidates = [
                    v for v in repo
                    if int(v.split('.')[0]) >= int(versions[driver_version]['min'])
                    and int(v.split('.')[0]) <= int(versions[driver_version]['max'])
                ]
                version = candidates[-1] if len(candidates) > 0 else None
                if version is None:
                    raise RuntimeError('No firefox esr version available')
            bits = 64 if maxsize > 2**32 else 32
            if platform.startswith('linux'):
                if bits == 64:
                    identifier = 'linux-x86_64'
                else:
                    identifier = 'linux-i686'
                file = 'firefox-%sesr.tar.bz2' % version
            elif platform == 'win32':
                identifier = 'win%s' % bits
                file = 'Firefox Setup %sesr.exe' % version
            elif platform == 'darwin':
                identifier = 'mac'
                file = 'Firefox %sesr.pkg' % version
            url = Firefox.URL_RELEASES % ('%sesr/%s/%s/%s' % (version, identifier, locale, file))
            path = join(PATH_RESOURCES, file)
            download_file(url, path)
            target = join(PATH_RESOURCES, 'firefox', driver_version)
            if not exists(target):
                mkdir(join(PATH_RESOURCES, 'firefox', driver_version))
            if platform == 'win32':
                run([join(PATH_RESOURCES, '7-zip', '7za.exe'), 'x', path, '-o' + join(PATH_RESOURCES, 'firefox'), '-y'])
                remove(join(PATH_RESOURCES, 'firefox', 'setup.exe'))
                remove(path)
                files = glob(join(PATH_RESOURCES, 'firefox', 'core', '*'), recursive=True)
                for file in files:
                    file_name = basename(file)
                    move(file, join(target, file_name))
                rmdir(join(PATH_RESOURCES, 'firefox', 'core'))
                exec_path = join(target, 'firefox.exe')
            elif platform.startswith('linux'):
                from bz2 import open as open_bz2
                from tarfile import open as open_tar
                with open_bz2(path, 'rb') as i, open(join(target, 'firefox.tar'), 'wb') as o:
                    copyfileobj(i, o)
                with open_tar(join(target, 'firefox.tar')) as i:
                    i.extractall(target)
                remove(join(target, 'firefox.tar'))
                rename(join(target, 'firefox'), join(target, 'firefox-%s' % driver_version))
                files = glob(join(target, 'firefox-%s' % driver_version, '*'), recursive=True)
                for file in files:
                    file_name = basename(file)
                    move(file, join(target, file_name))
                rmdir(join(target, 'firefox-%s' % driver_version))
                exec_path = join(target, 'firefox')
            elif platform == 'darwin':
                # TODO: Implement download for MacOS
                raise NotImplementedError('MacOS firefox auto-download support feature is a pending feature')
            else:
                raise RuntimeError('Platform %s not recognised.' % platform)
        else:
            raise RuntimeError('Gecko driver version is invalid or unrecognized')
        return exec_path

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
