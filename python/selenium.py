
from selenium import webdriver
from selenium.webdriver import ActionChains  #模拟鼠标事件

web=webdriver.Chrome('E:/Toolkit/chromedriver.exe')
web.get('http://www.baidu.com')  #打开网页
web.back()
#web.forward()
web.maximize_window()     #最大化窗口
web.set_window_size(480,800) #宽480，高800
print(web.title,web.current_url,web.page_source)  #sel=Selector(text=driver.page_source)
print(web.get_cookies())
print(type(web))                  #<class 'WebDriver'>
web.add_cookie({'name':'Login_UserNumber', 'value':'username'})
web.add_cookie({'name':'Login_Passwd', 'value':'password'})

input=web.find_element_by_xpath('//*[@id="kw"]')
'''
find_element只匹配第一个,find_elements匹配所有
find_element_by_link_text('continue'),需要完全匹配
find_element_by_partial_link_text('conti'),只需要部分匹配
find_element_by_id,find_element_by_name,find_elements_by_xpath...
'''
print(type(input))                  #<class 'WebElement'>
print(input.id)   #利用ID判断元素是否相同
input.clear()
input.send_keys('fuck u!!')    #clear send_keys要同时使用
submit=web.find_element_by_xpath('//*[@id="su"]')
print(submit .get_attribute('id'))
submit.click()

################################################################################################################

from selenium import webdriver
from selenium.webdriver.support.select import Select
driver=webdriver.Chrome('e:/toolkit/chromedriver.exe')
driver.get('http://query.customs.gov.cn/MNFTQ/MQuery.aspx')
driver.find_element_by_xpath('//*[@id="MQueryCtrl1_ddlCustomCode"]/option[48]').click()
sel = driver.find_element_by_xpath('//*[@id="MQueryCtrl1_ddlCustomCode"]')
Select(sel).select_by_value('0217') #下拉框有value属性,等价
#Select(sel).select_by_index('0217') #下拉框有index属性
driver.find_elements_by_css_selector('input[type=checkbox]').pop().click()

################################################################################################################

测试麦子学院
web.get('http://www.maiziedu.com')
ele=web.find_element_by_xpath('//ul[@class="fl top_menu"]/li')
print(ele.text)     #企业直通班
ActionChains(web).move_to_element(ele).perform()
ele1=web.find_element_by_xpath('//div[@class="pcon"]/a[@href="/course/te-px/"]')
print(ele1.text)     #软件测试
ele1.click()

################################################################################################################

测试QQ
driver.get("http://i.qq.com/")
driver.switch_to_frame('login_frame')
driver.find_element_by_xpath('//*[@id="switcher_plogin"]').click()
user=driver.find_element_by_xpath('//*[@id="u"]')
user.clear()
user.send_keys('212956978')
pwd=driver.find_element_by_xpath('//*[@id="p"]')
pwd.clear()
pwd.send_keys('pass')
driver.find_element_by_xpath('//*[@id="login_button"]').click()
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  #拖动滚动条到最下面
driver.execute_script("window.scrollTo(0, 0);")
element = driver.execute_script("return $('.cheese')[0]")

################################################################################################################

selenium操作隐藏元素会报错
exceptions.ElementNotVisibleException: Message: element not visible: Element is not currently visible and may not be manipulated
解决方法: 
driver.execute_script('$("select").attr("style","display:block");') 
比如网页的select的style属性是display:none(隐藏),必须改成block才能后续操作
web.implicitly_wait(10)  #全局有效,一旦找到立马返回,WebDriverWait针对一个操作
web.get('https://www.baidu.com/s?wd=%E9%BA%A6%E5%AD%90%E5%AD%A6%E9%99%A2')
web.find_element_by_partial_link_text('麦子学院 - 专业IT职业在线教育平台').click()
print(web.window_handles,web.current_window_handle)
web.switch_to.window(web.window_handles[1])

################################################################################################################

有时候为了保证脚本运行的稳定性,需要脚本中添加等待时间
sleep(): 设置固定休眠时间
implicitly_wait(): 隐的等待一个元素被发现,或一个命令完成,如果超出了设置时间的则抛出异常
WebDriverWait(): 在设置时间内,默认每隔一段时间检测一次当前页面元素是否存在,如果超过设置时间检测不到则抛出异常
详细格式如下:
WebDriverWait(driver, timeout, poll_frequency=0.5, ignored_exceptions=None)
driver  - WebDriver的驱动程序(IE, Firefox, Chrome 或远程)
timeout - 最长超时时间,默认以秒为单位
poll_frequency - 休眠时间的间隔(步长)时间,默认为0.5秒
ignored_exceptions - 超时后的异常信息,默认情况下抛NoSuchElementException异常
WebDriverWait()一般由unit()或until_not()方法配合使用
until(method, message=’ ’)     调用该方法提供的驱动程序作为一个参数,直到返回值不为False
until_not(method, message=’ ’) 调用该方法提供的驱动程序作为一个参数,直到返回值为False
下面通过实例来展示方法的具体使用:
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
NUM=5
HONGCHOU='https://www.3658mall.com/hongchou-detail-202.html'  #205
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--user-data-dir=chrome')
web = webdriver.Chrome(chrome_options=options,executable_path='/opt/google/chrome/chromedriver')
web.get('https://www.3658mall.com/member.html')
try:
    name=web.find_element_by_xpath('//input[@id="username"]')
    name.clear()
    name.send_keys('name')
    pwd=web.find_element_by_xpath('//input[@id="password"]')
    pwd.clear()
    pwd.send_keys('password')
    web.find_element_by_xpath('//input[@id="remember"]').click()
    web.find_element_by_xpath('//input[@id="login_submit"]').click()
except:
    pass
web.get(HONGCHOU) 
while True:
    try:
        WebDriverWait(web, 1,.3).until(lambda web : web.find_element_by_id("snum"))   
        web.execute_script(f"$('#snum').val({NUM})")
        web.find_element_by_xpath('//*[@class="btn btn_red conpons_chips_buy"]').click()
        WebDriverWait(web, 1,.3).until(lambda web : web.find_element_by_xpath(f'//*[@data-rule-num="{NUM}"]'))
        web.execute_script(f"$('a[data-rule-num={NUM}]').click()")
        # web.save_screenshot('3658.png')   # 方便调试
        web.quit()
        web.close() #只关闭当前窗口
        break
    except:
        web.refresh()
