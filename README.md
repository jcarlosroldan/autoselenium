# AutoSelenium: Selenium without any hassle

This Python 3 library solves most of the tasks that are usually related to use Selenium in a project. The main features of this library are:

* Full Selenium compatibility: the automatic drivers inherit the Selenium driver, so every available functionality is preserved.
* Geckodriver management: the latest valid Geckodriver is automatically downloaded, unzipped and stored according to the Selenium version and operative system.
* Updated defaults: some of the most common driver configurations are automatically set, such as disabling Flash, ignoring the txt log file or closing the driver when the program ends. All of them can be edited via construction params.
* Rendering analysis: the rendering features such as computed style, width, height or XPath are added to the page source when using `driver.get_with_render` instead of `driver.get`.

Some features to be expected in the future are:

* Support for Chrome and Safari drivers.
* Automatic portable Firefox installation: it involves uncompressing zip, 7z, tar.gz, tar.bz2 and xar files.

## How to install


1. Install any of the geckodriver 0.26.0 Firefox supported versions (see [compatibility table](https://firefox-source-docs.mozilla.org/testing/geckodriver/Support.html))
2. Install this library via pip using: `pip install autoselenium`

## Usage example

```python
>>> from autoselenium import Firefox
>>>
>>> driver = Firefox(headless=True)
>>>
>>> driver.get('https://juancroldan.com')
>>> driver.find_element_by_tag_name('div').get_attribute('outerHTML')
'<div id="mw-page-base" class="noprint"></div>'
>>>
>>> driver.get_with_render('https://juancroldan.com')
>>> driver.find_element_by_tag_name('div').get_attribute('outerHTML')
'<div id="mw-page-base" class="noprint"\
	data-xpath="/html[1]/body[1]/div[1]"\
	data-computed-style="align-content:normal;align-items:normal;...;z-index:auto"\
	data-width="1356" data-height="80"\
	data-width-rel="1" data-height-rel="0.11527377521613832"></div>'
```

This library only have one class: `Firefox`, a child of `selenium.drivers.Firefox` with extended construction parameters:

`Firefox(headless=False, detect_driver_path=True, disable_images=True, disable_flash=True, open_links_same_tab=False, timeout=15, version='0.26.0', options=None, *args, **kwargs)`

* `headless: bool`: When true, the Firefox interface won't be shown.
* `detect_driver_path: bool`: When true, geckodriver will be automatically located and downloaded.
* `disable_images: bool`: When true, images won't be loaded to improve the performance.
* `disable_flash: bool`: When true, Flash will be disabled.
* `open_links_same_tab: bool`: When true, even new tab links will be opened in the same tab.
* `timeout: int`: Page load timeout.
* `version: str`: If `detect_driver_path` is set, this geckodriver version will be downloaded. When a new geckodriver is relased, it is tested with the latest Selenium version to use the most recent compatible version.

It also implements one extra function, `driver.get_with_render(url, render_selector='body')`, which works the same way as `driver.get(url)`, processing the nodes selected by `render_selector` with a few rendering operations:

* Nodes without rendering are removed.
* For every node and child, a few `data-` properties are added:
	* `data-xpath`: XPath of the node.
	* `data-computed-style`: Computed style of the nodes, using the same notation of the `style` element attribute.
	* `data-width`: Width of the node.
	* `data-height`: Height of the node.
	* `data-width-rel`: Width of the node relative to the page width.
	* `data-height-rel`: Height of the node relative to the page height.

## Changes

### v0.0.

Released on Oct 10, 2019.

* Initial package upload.
* Removed table-specific features.