# AutoSelenium: Ready-to-run Selenium

This Python 3 library solves most of the tasks that are usually related to use Selenium in a project.

## Installing

1. Install a version of Firefox compatible with geckodriver 0.26.0 (see this [compatibility table](https://firefox-source-docs.mozilla.org/testing/geckodriver/Support.html))
2. Install this library via pip using: `pip install autoselenium`

## Usage

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

* `headless`: A boolean, False by default. When true, the Firefox interface won't be shown.
* `detect_driver_path`: A boolean, True by default. When true, geckodriver will be automatically located and downloaded.
* `disable_images`: A boolean, True by default. When true, images won't be loaded to improve the performance.
* `disable_flash`: A boolean, True by default. When true, Flash will be disabled.
* `open_links_same_tab`: A boolean, False by default. When true, even new tab links will be opened in the same tab.
* `timeout`: An integer, 15 by default. Page load timeout.
* `version`: A string, 0.26.0 by default. If `detect_driver_path` is set, this geckodriver version will be downloaded. When a new geckodriver is relased, it is tested with the latest Selenium version to use the most recent compatible version.
* Any of the [Selenium Firefox parameters](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_firefox/selenium.webdriver.firefox.webdriver.html#module-selenium.webdriver.firefox.webdriver).

It also implements one extra function, `driver.get_with_render(url, render_selector='body')`, which works the same way as `driver.get(url)`, processing the nodes selected by `render_selector` with a few rendering operations:

* Nodes without rendering are removed.
* For every node and child, a few data properties are added:
	* `data-xpath`: XPath of the node.
	* `data-computed-style`: Computed style of the nodes, using the same notation of the `style` element attribute.
	* `data-width`: Width of the node.
	* `data-height`: Height of the node.
	* `data-width-rel`: Width of the node relative to the page width.
	* `data-height-rel`: Height of the node relative to the page height.

## Features

* Full Selenium compatibility: the automatic drivers inherit the Selenium driver, so every available functionality is preserved.
* Geckodriver management: a valid Geckodriver is automatically downloaded, unzipped and stored according to the Selenium version and operative system.
* Updated defaults: some of the most common driver configurations are automatically set, such as disabling Flash, ignoring the txt log file or closing the driver when the program ends. All of them can be edited via construction params.
* Rendering analysis: the rendering features such as computed style, width, height or XPath are added to the page source when using `driver.get_with_render` instead of `driver.get`.

## Contributions ✨

You can take any of the pending [enhancements](https://github.com/juancroldan/autoselenium/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement), work on it and open a pull request.

## Changes

### v0.1.0

Relased on Oct 28, 2019.

* More helpful exceptions (including install exceptions).
* Friendlier readme.
* Bugfix: now compatible with any Python 3 library.

### v0.0.1

Released on Oct 10, 2019.

* Initial package upload.
* Removed table-specific features.