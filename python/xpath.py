from lxml.html import fromstring, tostring

################################################################################################################
"""
lxml.etree
XML processing
lxml.html
Since version 2.0, lxml comes with a dedicated Python package for dealing with HTML: lxml.html.It is based on lxml's HTML parser, 
but provides a special Element API for HTML elements,as well as a number of utilities for common HTML processing tasks.
The main API is based on the lxml.etree API, and thus, on the ElementTree API.
"""

################################################################################################################
'''
Avoid using contains(.//text(), ‘search text’) in your XPath conditions. Use contains(., 'search text') instead.
You can read more detailed explanations about string values of nodes and node-sets in the XPath spec.
Here is why:
the expression .//text() yields a collection of text elements — a node-set.
And when a node-set is converted to a string, which happens when it is passed as argument 
to a string function like contains() or starts-with(), results in the text for the first element only.
节点下标是从1开始的,类似的还有last(),last()-1,position()<3等等
'''

web = '<a href="#">Click here to go to the <strong>Next Page</strong></a>'
res = fromstring(web)
print(res.xpath('//a//text()'))  # ['Click here to go to the ', 'Next Page']
print(res.xpath('string(//a//text())'))  # Click here to go to the
print(res.xpath('//a[1]'))  # [<Element a at 0x19a10890cc8>]
print(res.xpath('string(//a[1])'))  # Click here to go to the Next Page

print(res.xpath('//a[contains(., "Page")]'))  # .表示当前节点的内容
print(res.xpath('//a[starts-with(., "Click")]'))  # .表示当前节点的内容，ends-with类似
print(res.xpath('//a[contains(.//text(), "Page")]'))  # []

################################################################################################################
'''
Beware of the difference between //node[1] and (//node)[1]
//node[1] selects all the nodes occurring first under their respective parents.
(//node)[1] selects all the nodes in the document, and then gets only the first of them.
优先级[]大于//
'''

web = """
  <ul class="list">
    <li>1</li>
    <li>2</li>
    <li>3</li>
  </ul>
  <ul class="list">
    <li>4</li>
    <li>5</li>
    <li>6</li>
  </ul>
"""
res = fromstring(web)
# get all first LI elements under whatever it is its parent
print(res.xpath('//li[1]/text()'))  # ['1', '4']
# get all first LI elements under an UL parent
print(res.xpath('//ul/li[1]/text()'))  # ['1', '4']

# get the first LI element in the whole document
print(res.xpath('(//li)[1]/text()'))  # ['1']
# get the first LI element under an UL parent in the document
print(res.xpath('(//ul/li)[1]/text()'))  # ['1']
print(res.text_content())  # 获取文本内容

################################################################################################################
'''
When selecting by class, be as specific as necessary
If you want to select elements by a CSS class, the XPath way to do that is the rather verbose:
'''

web = '''
  <p class="content-author">Someone</p>
  <div class="content text-wrap">Some content</div>
'''
res = fromstring(web)
print(res.xpath('//*[@class="content"]/text()'))  # []   注意
print(res.xpath('//*[@class="content text-wrap"]/text()'))  # ['Some content']
print(res.xpath('//*[contains(@class,"content")]/text()'))  # ['Someone', 'Some content']
# '<div class="content text-wrap">Some content</div>\n'
print(tostring(res.xpath('//*[@class="content text-wrap"]')[0], encoding='unicode'))  # encoding防止中文被转意

################################################################################################################
'''
and or |
'''

web = """
    <ul>
      <li class="item-0" name='test-0'>
        <a href="link1.html">first item</a>
      </li>
      <li class="item-0" name='test-1'>
        <a href="link2.html">second item</a>
      </li>
      <li class="item-inactive">
        <a href="link3.html">third item</a>
      </li>
    </ul>
"""
res = fromstring(web)
print(res.xpath('//li[@class="item-0" and @name="test-1"]'))  # [<Element li at 0x1c4e93e97c8>]
print(res.xpath(
    '//li[@class="item-0" or @name="test-1"]'))  # [<Element li at 0x1c4e93e97c8>, <Element li at 0x1c4e93f06d8>]
print(res.xpath('//li | //a'))  # 选取所有的li标签和a标签,注意这里的|是指选取所有符合条件标签
