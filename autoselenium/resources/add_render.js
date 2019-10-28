function pathTo(element) {
	if (element === document) return ''
	var ix = 0
	var siblings = element.parentNode.childNodes
	for (var i = 0; i < siblings.length; i++) {
		if (siblings[i] === element) return pathTo(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']'
		if (siblings[i].nodeType === 1 && siblings[i].tagName === element.tagName) ix++
	}
}

var removeElements = []
function addRender(subtree) {
	var style = getComputedStyle(subtree)
	// ignore nodes without an actual representation
	if (style['display'] == 'none' || subtree.offsetWidth == undefined || subtree.tagName == 'TR' && subtree.children.length == 0) {
		removeElements.push(subtree)
		return
	}
	// get every css property ignoring the vendor-prefixed properties
	var serialStyle = ''
	for (let prop of style) {
		if (prop[0] != '-') {
			serialStyle += prop + ':' + style[prop].replace(/[:;]/g, '') + ';'
		}
	}
	serialStyle = serialStyle.substring(0, serialStyle.length - 1)

	subtree.setAttribute('data-xpath', pathTo(subtree).toLowerCase())
	subtree.setAttribute('data-computed-style', serialStyle)
	subtree.setAttribute('data-width', subtree.offsetWidth)
	subtree.setAttribute('data-height', subtree.offsetHeight)
	subtree.setAttribute('data-width-rel', subtree.offsetWidth / document.body.offsetWidth)
	subtree.setAttribute('data-height-rel', subtree.offsetHeight / document.body.offsetHeight)

	for (let child of subtree.children) addRender(child)
}

function preprocess() {
	var elements = document.querySelectorAll(injected_script_selector)
	for (let subtree of elements) addRender(subtree)
	for (let elem of removeElements) elem.remove()
}

const injected_script_selector = arguments[0]

if (document.readyState == 'complete') {
	preprocess()
} else {
	window.onload = function(){preprocess()}
}