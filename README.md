# AutoSelenium: Zero-Setup Selenium

This Python 3 library eliminates all setup headaches when using Selenium by automatically downloading and managing both Firefox and geckodriver.

## Installing

```bash
pip install autoselenium
```

That's it! No manual downloads, no PATH configuration, no compatibility checking.

## Usage

```python
>>> from autoselenium import Firefox
>>> from selenium.webdriver.common.by import By
>>>
>>> # Uses system Firefox with auto-downloaded geckodriver
>>> driver = Firefox(headless=True)
>>>
>>> driver.get('https://example.com')
>>> driver.find_element(By.TAG_NAME, 'div').get_attribute('outerHTML')
'<div><h1>Example Domain</h1><p>This domain is for use in illustrative examples...</p></div>'
>>>
>>> # Add rendering data to elements
>>> driver.get_with_render('https://example.com')
>>> driver.find_element(By.TAG_NAME, 'div').get_attribute('outerHTML')
'<div data-xpath="/html[1]/body[1]/div[1]" data-computed-style="display:block;margin:0px;..." data-width="1200" data-height="600" data-width-rel="1" data-height-rel="0.5">...'
>>>
>>> # Use specific browser and driver versions
>>> driver = Firefox(browser_detection=True, browser_version='120.0', driver_version='0.35.0')
>>>
>>> driver.quit()
```

## Parameters

The `Firefox` class extends `selenium.webdriver.Firefox` with these additional parameters:

* `browser_detection`: Boolean, False by default. When True, downloads and uses a specific Firefox version instead of system Firefox.
* `browser_version`: String, 'default' by default. Firefox version to download. Use 'default' for latest stable version.
* `driver_detection`: Boolean, True by default. When True, automatically downloads the appropriate geckodriver.
* `driver_version`: String, None by default. Geckodriver version to use. When None, uses latest version.
* `headless`: Boolean, False by default. When True, runs Firefox without a GUI.
* `disable_images`: Boolean, True by default. When True, disables image loading for better performance.
* `disable_flash`: Boolean, True by default. When True, disables Flash plugin.
* `open_links_same_tab`: Boolean, False by default. When True, forces all links to open in the same tab.
* `timeout`: Integer, 30 by default. Page load timeout in seconds.
* `options`: Firefox Options object, None by default. Custom Firefox options (merged with above settings).

All standard [Selenium Firefox parameters](https://selenium-python.readthedocs.io/api.html#selenium.webdriver.firefox.webdriver.WebDriver) are also supported.

## Methods

### `get_with_render(url, render_selector='body')`

Works like `driver.get(url)` but adds rendering metadata to elements selected by `render_selector`:

* **`data-xpath`**: XPath of the element
* **`data-computed-style`**: Full computed CSS styles
* **`data-width`**: Element width in pixels
* **`data-height`**: Element height in pixels  
* **`data-width-rel`**: Width relative to page width (0-1)
* **`data-height-rel`**: Height relative to page height (0-1)

Elements without rendering (display:none, etc.) are automatically removed.

## Features

### 🚀 **Zero Configuration**
- Automatically downloads geckodriver for your platform (including ARM64)
- Optionally downloads Firefox itself for complete version control
- Works out of the box on Windows, macOS, and Linux

### 🔄 **Smart Version Management** 
- Automatically uses latest geckodriver and Firefox versions
- Caches downloads to avoid re-downloading
- Supports manual version pinning for reproducible environments

### 🏗️ **Platform Support**
- **Full ARM64 support** (Apple Silicon, Raspberry Pi, etc.)
- All major platforms: Windows (32/64/ARM64), macOS (Intel/ARM64), Linux (32/64/ARM64)
- Solves the platform compatibility issues that break vanilla Selenium

### ⚡ **Performance Optimized**
- Images disabled by default for faster loading
- Progress bars for large downloads (using tqdm)
- Efficient caching prevents redundant downloads

### 🔧 **Developer Friendly**
- Full Selenium 4 compatibility
- Modern Python API (no deprecated methods)
- Automatic cleanup on exit
- Rich rendering analysis tools

## Requirements

- Python 3.7+
- requests
- selenium >= 4.0
- tqdm

## Platform-Specific Notes

### **Raspberry Pi / ARM64 Systems**
AutoSelenium specifically solves ARM64 compatibility issues that break standard Selenium:

```python
# This fails on ARM64 with vanilla Selenium
driver = webdriver.Firefox()  # ❌ "Unsupported platform/architecture combination"

# This works perfectly with AutoSelenium  
driver = Firefox()  # ✅ Downloads ARM64 geckodriver automatically
```

### **Isolated Environments**
Perfect for Docker, CI/CD, or any environment where you can't install Firefox:

```python
# Downloads everything needed automatically
driver = Firefox(browser_detection=True, headless=True)  # ✅ Completely self-contained
```

## Examples

### Basic Web Scraping
```python
from autoselenium import Firefox
from selenium.webdriver.common.by import By

driver = Firefox(headless=True)
driver.get('https://example.com')
title = driver.find_element(By.TAG_NAME, 'h1').text
print(f'Page title: {title}')
driver.quit()
```

### Version-Controlled Testing
```python
# Pin exact versions for reproducible tests
driver = Firefox(
    browser_detection=True,
    browser_version='119.0',
    driver_version='0.34.0',
    headless=True
)
```

### Rendering Analysis
```python
driver = Firefox()
driver.get_with_render('https://example.com')

# Find all visible elements with their dimensions
elements = driver.find_elements(By.CSS_SELECTOR, '[data-width]')
for el in elements:
    width = el.get_attribute('data-width')
    height = el.get_attribute('data-height') 
    xpath = el.get_attribute('data-xpath')
    print(f'{xpath}: {width}x{height}px')
```

## Troubleshooting

### Downloads Failing
If downloads fail, check your internet connection and try:
```python
# Use specific versions instead of 'default'
driver = Firefox(browser_version='120.0', driver_version='0.34.0')
```

### Permission Errors
Ensure the script has write permissions to the package directory, or run:
```bash
pip install --user autoselenium
```

## Contributing

Found a bug or want to add a feature? Check out the [issues](https://github.com/juancroldan/autoselenium/issues) and submit a pull request!

## Changelog

### v1.0.0 (2024)

**Major Rewrite - Breaking Changes**
- 🚀 **Full ARM64 support** (Apple Silicon, Raspberry Pi)
- 🔄 **Automatic browser downloads** with `browser_detection=True`
- ⚡ **Latest version detection** for both Firefox and geckodriver
- 🛠️ **Selenium 4 compatibility** (updated from Selenium 3)
- 📊 **Download progress bars** using tqdm
- 🧹 **Simplified API** with better parameter names
- 🌐 **Extended platform support** (Windows ARM64, Linux ARM64)

**Breaking Changes from v0.x:**
- Parameter `detect_driver_path` → `driver_detection` 
- Parameter `version` → `driver_version`
- Requires Selenium 4+ and Python 3.7+
- Default timeout increased from 15s to 30s

### v0.1.0 (2019)

- More helpful exceptions
- Python 3 compatibility fixes
- Documentation improvements

### v0.0.1 (2019)

- Initial release
- Basic geckodriver management