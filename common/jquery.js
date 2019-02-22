jQuery把所有功能全部封装在一个全局变量jQuery中,而$也是一个合法的变量名,它是变量jQuery的别名.
typeof($)   //function
alert($===jQuery)  //true
var sowhat=jQuery.noConflict();    #防止$符冲突

约定俗成: 定义jQuery对象时变量名以$开头,其他变量则相反
var $cr = $("#cr");
var cr  = $cr[0];
var cr = doucument.getElementById("cr");
var $cr = $(cr);

如果网页上某个标签无法被事件监听,可能是被其他元素的margin挡住了

使用submit前提:
必须由form的筛选器来调用submit
必须有submit按钮或者input的type=submit来触发
<input class='save' type="submit" data-value="0" value="保存">

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

<script>
$(function(){        

  console.time('test');
  var tmp='';
  for(let i=0;i<15000;i++){
    tmp+='<li><span>Haskell</span></li>';
  }
  $('#myDiv1').append(tmp);   //尽量避免对DOM的操作次数
  console.timeEnd('test');

});
</script>

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

$( xxx ).serialize()
The .serialize() method creates a text string in standard URL-encoded notation.It can act on a jQuery object that has selected individual form controls, 
such as <input>, <textarea>, and <select>: $( "input, textarea, select" ).serialize();
您可以选择一个或多个表单元素(比如 input 及/或 文本框)或者 form 元素本身,其他标签则无效.
It is typically easier, however, to select the <form> itself for serialization:
$( "form" ).on( "submit", function( event ) {
  event.preventDefault();    //阻止默认行为
  console.log( $( this ).serialize() );
});

<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<script>

$(function(){
  $('form').submit(function(){
   alert($('form').serialize())   //"a=1&b=2&c=3&d=4&e=5"
  })
});

</script>

<form>
  <div><input type="text" name="a" value="1" id="a" /></div>
  <div><input type="text" name="b" value="2" id="b" /></div>
  <div><input type="hidden" name="c" value="3" id="c" /></div>
  <div>
    <textarea name="d" rows="8" cols="40">4</textarea>
  </div>
  <div><select name="e">
    <option value="5" selected="selected">5</option>
    <option value="6">6</option>
    <option value="7">7</option>
  </select></div>
  <div>
    <input type="checkbox" name="f" value="8" id="f" />
  </div>
  <div>
    <input type="submit" name="g" value="Submit" id="g" />
  </div>
</form>

//只会将"成功的控件"序列化为字符串
//如果要表单元素的值包含到序列字符串中,元素必须使用 name 属性

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

$("#elem").click(function(){})  //快捷方式
$("#elem").on('click',function(){}) //on方式

多个事件绑定同一个函数
$("#elem").on("mouseover mouseout",function(){ });
通过空格分离,传递不同的事件名,可以同时绑定多个事件

多个事件绑定不同函数
$("#elem").on({
mouseover:function(){},
mouseout:function(){},
});
通过空格分离,传递不同的事件名,可以同时绑定多个事件,每一个事件执行自己的回调方法

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

$( xxx ).each()
<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<style>
  div {
    width: 40px;
    height: 40px;
    margin: 5px;
    float: left;
    border: 2px darkred solid;
    text-align: center;
  }
  span {
    color: red;
  }
</style>

<button>Change colors</button>
<span></span>
<div>1</div>
<div>2</div>
<div id="stop">Stop here</div>
<div>3</div>
<div>4</div>

<script>
$(function(){

//$( "button" ).click(function() {
//  $( "div" ).each(function(index) {
//    console.log($(this).text())  //$(this)指向每一个遍历的div
//    $( this ).css( "backgroundColor", "yellow" );
//    if ( $( this ).attr('id') ==='stop') {
//      $( "span" ).text( "Stopped at div index " + index );
//      return false;   //Use return false to break out of each() loops early.
//    }
//  });
//}); 


$( "button" ).click(function() {
  for(let div of $( "div" )){
    console.log($(div).text())
    $(div).css( "backgroundColor", "yellow" );
    if ( div.id ==='stop') {
      $( "span" ).text( "Stopped at div " + div );
      break;
    }
  }   
});

});
</script>

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

Ajax与传统表单提交的区别
1. Ajax在提交、请求、接收时,都是异步进行的,网页不需要刷新;
   Form提交则是新建一个页面;
2. A在提交时,是在后台新建一个请求;
   F却是放弃本页面,而后再请求;
3. A必须要使用JS来实现,不启用JS的浏览器,无法完成该操作;
   F却是浏览器的本能,无论是否开启JS,都可以提交表单;
4. A在提交、请求、接收时,整个过程都需要使用程序来对其数据进行处理;
   F提交时,却是根据你的表单结构自动完成,不需要代码干预;

Ajax全局设置
$.ajaxSetup({
    data: {csrfmiddlewaretoken: '{{ csrf_token }}' },
});

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

$.post()
var jqxhr = $.post( "example.php", { name: "John", time: "2pm" }, function(data) {
  alert( "success" );
}, "json")
  .done(function() {
    alert( "second success" );
  })
  .fail(function() {
    alert( "error" );
  })
  .always(function() {
    alert( "finished" );
});

// Perform other work here ...
// Set another completion function for the request above

jqxhr.always(function() {
  alert( "second finished" );
});

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

$.get()
var jqxhr = $.get( "example.php", {name:'John',time:'2pm'},function(data) {
  alert( "success" );
}, "json" )
  .done(function(data) {
    alert( "second success" );
  })
  .fail(function() {
    alert( "error" );
  })
  .always(function() {
    alert( "finished" );
  });

// Perform other work here ...
// Set another completion function for the request above

jqxhr.always(function() {
  alert( "second finished" );
});

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

$ & $.fn
<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<script>
    $(function() {
        $.myadd = function(a, b) {  //添加静态方法
            return a + b;
        }
        ;
        $.fn.mymax = function(a, b) {  //为jQuery类添加"成员函数"
            return a > b ? a : b;
        }
        $('button').click(function() {
            alert($.myadd(3, 5));
            alert($('button').mymax(3, 5));
        })
    });
</script>
<button>Click Me!</button>

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

$.extend()
<html>
    <script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
    <script>
        var object1 = {
            apple: 0,
            banana: {
                weight: 52,
                price: 100
            },
            cherry: 97
        };
        var object2 = {
            banana: {
                price: 200
            },
            durian: 100
        };

        $(function() {
            $('button').click(function() {

                // Merge object2 into object1
                //$.extend(object1, object2); 
                //console.log(object1); //{"apple":0,"banana":{"price":200},"cherry":97,"durian":100}

                // Merge object2 into object1, recursively(递归合并)
                $.extend( true, object1, object2 );
                //console.log(object1);  //{"apple":0,"banana":{"weight":52,"price":200},"cherry":97,"durian":100}

                // Merge object1 and object2, without modifying object1
                $.extend( {}, object1, object2 );

            });
        })

    </script>
    <button>Download</button>
</html>

目标对象(第一个参数)将被修改,并且将通过$.extend()返回
默认情况下,$.extend()合并操作不是递归的;如果第一个对象的属性本身是一个对象或数组,那么它将完全用第二个对象相同的key重写一个属性
利用extend可以进行深拷贝
var a=[1,2,[3,4],{q:2}]
var b=$.extend([],a)

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

浏览器安全限制
在浏览器中,有些JavaScript代码只有在用户触发下才能执行,例如window.open()函数:
// 无法弹出新窗口,将被浏览器屏蔽:
$(function () {
    window.open('/');
});

这些"敏感代码"只能由用户操作来触发:
function popupTestWindow() {
    window.open('/');
}
$('#button1') .click(function () {
    popupTestWindow();
});

$('#button2') .click(function () {
    setTimeout(popupTestWindow, 100); // 不立刻执行popupTestWindow(),100毫秒后执行
});
当用户点击button1时,click事件被触发,由于popupTestWindow()在click事件处理函数内执行,这是浏览器允许的;
而button2的click事件并未立刻执行popupTestWindow(),延迟执行的popupTestWindow()将被浏览器拦截.

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

trigger:
一个需要注意的问题是,事件的触发总是由用户操作引发的,例如我们监控文本框的内容改动:
$('#test-input').change(function () {
    console.log('changed...');
});

当用户在文本框中输入时,就会触发change事件,如果用JavaScript代码去改动文本框的值,将不会触发change事件:
$('#test-input').val('change it!'); // 无法触发change事件

有些时候我们希望用代码触发change事件,可以直接调用无参数的change()方法来触发该事件:
var input = $('#test-input');
input.val('change it!');
input.change(); // 触发change事件
or
$('#test-input').val('change it!') .change(); 

input.change()相当于input.trigger('change'),它是trigger()方法的简写,但不能传递参数
为什么我们希望手动触发一个事件呢?如果不这么做，很多时候，我们就得写两份一模一样的代码.

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

取消绑定:
一个已被绑定的事件可以解除绑定,通过off('click', function)实现:
function hello() {alert('hello!');}
a.click(hello); // 绑定事件
// 10秒钟后解除绑定:
setTimeout(function () { a.off('click', hello);}, 10000);

下面这种写法无效:
// 绑定事件:
a.click(function () {
   alert('hello!');}
);
// 解除绑定:
a.off('click', function () {
   alert('hello!');}
);
这是因为两个匿名函数虽然长得一模一样,但是它们是两个不同的函数对象,off('click', function () {...})无法移除已绑定的第一个匿名函数
为了实现移除效果,可以使用off('click')一次性移除已绑定的click事件的所有处理函数,同理无参数调用off()一次性移除已绑定的所有类型的事件处理函数

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

提交事件:
如果你遇到$(function () {...})的形式,牢记这是document对象的ready事件处理函数,目的是保证DOM已完成初始化.
$(function() {
     $('#testForm').submit(function () {
         alert('aaaaaa');
         $(this).hide(1000);    # $(this)指向$('#testForm')
     });
});

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

事件委托 & 事件对象:
ul有N个子元素li(这里只写了3个),因为li都有一个共同的父元素,而且所有的事件都是一致的,这里我们可以采用要一个技巧来处理,也是常说的"事件委托"
由于浏览器有事件冒泡的这个特性,我们可以在触发li的时候把这个事件往上冒泡到ul上,因为ul上绑定事件响应所以就能够触发这个动作了
如何知道触发的li元素是哪个一个?
这里就引出了事件对象(event)，事件对象只有事件发生时才会产生，并且只能是事件处理函数内部访问,在所有事件处理函数运行结束后,事件对象就被销毁
event.target属性可以是注册事件时的元素,或者它的子元素,通常用于比较event.target和this来确定事件是不是由于冒泡而触发的
简单来说,event.target代表当前触发事件的元素,可以通过当前元素对象的一系列属性来判断是不是我们想要的元素
<head>
    <meta charset="utf-8">
    <script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
    <script>
      $(function(){

        $("ul").click(function(event,param){
          alert('触发的元素内容是: ' + event.target.textContent+'\n传递过来的参数是:'+param);
        })

        //手动触发事件用trigger
        $('ul').trigger('click','this is the test for trigger!')
      })
    </script>
</head>

<h3>事件委托,通过事件对象区别触发元素</h3>
<ul>
  <li>触发一</li>
  <li>触发二</li>
  <li>触发三</li>
</ul>

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

事件对象的属性和方法:
<meta charset='utf-8'>
<style>
div{
  width:150px;
  height:50px;
  line-height:50px;
  text-align:center;
  border:1px dashed darkred; 
}
</style>
<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<script>
$(function(){
  /*
  点击a标签{Baidu一下,test Baidu一下,click,94 36}
  点击div标签{test Baidu一下,test Baidu一下,click,94 36}
  */
  $('div').click(function(){
    console.log(event.target.textContent);        //直接接受事件的目标DOM元素
    console.log(event.currentTarget.textContent); //在事件冒泡过程中的当前DOM元素,此处this和event.currentTarget等价，且都是DOM对象,等价于$(this).text()
    console.log(event.type);                      //事件类型
    console.log(event.pageX,event.pageY);         //鼠标当前相对于页面的坐标,不随滑动条移动而变化
    return false;                                 //阻止浏览器默认行为(event.preventDefault, event.stopPropagation ),此处即阻止a标签跳转
  })

})
</script>

<div>
  test&nbsp;<a href='http://www.baidu.com' target='_blank'>Baidu一下</a>
</div>

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

鼠标事件
click: 鼠标单击时触发
dblclick: 鼠标双击时触发
mouseenter: 鼠标进入时触发
mouseleave: 鼠标移出时触发
mousemove: 鼠标在DOM内部移动时触发
hover: 鼠标进入和退出时触发两个函数,相当于mouseenter加上mouseleave
键盘事件
键盘事件仅作用在当前焦点的DOM上,通常是<input>和<textarea>
keydown: 键盘按下时触发
keyup: 键盘松开时触发,动态判断用户输入的内容(应为用户第一个文字输入的内容只能被keyup检测到),如检测密码长度
keypress: 按一次键后触发
其他事件
focus: 当DOM获得焦点时触发
blur: 当DOM失去焦点时触发
change: 当<input>、<select>或<textarea>的内容改变时触发
submit: 当<form>提交时触发
ready: 当页面被载入并且DOM树完成初始化后触发

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

data():
<!--
新的HTML5标准允许你在普通的元素标签里,嵌入类似data-*的属性,来实现一些简单数据的存取
它的数量不受限制,并且也能由javascript动态修改,也支持CSS选择器进行样式设置
-->

<div data-url='http://www.baidu.com'>test</div>
<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<script>
$(function(){
  console.log($('div').attr('data-url'));   //http://www.baidu.com
  console.log($('div').data('url'));        //http://www.baidu.com
  $('div').data({name:'avatar',prop:{id:1,nickname:'jesus'}});  //不会反映在网页源代码上
  console.log($('div').data('name'));       //avatar
  console.log($('div').attr('data-name'));  //undefined
   console.dir($('div').data('prop')['id']);  //1
  console.dir($('div').data()['prop']['id']);  //1
});
</script>

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

对于表单元素,jQuery对象统一提供val()方法获取和设置对应的value属性:
<input id="test-input" name="email" value="">

<select id="test-select" name="city">
    <option value="BJ" selected>Beijing</option>
    <option value="SH">Shanghai</option>
    <option value="SZ">Shenzhen</option>
</select>
<textarea id="test-textarea">Hello</textarea>

<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<script>
    var input = $('#test-input');
    var select = $('#test-select');
    var textarea = $('#test-textarea');

    console.log(input.val()); // ''
    input.val('abc@example.com'); // 文本框的内容已变为abc@example.com

    console.log(select.val()); // 'BJ'
    select.val('SH'); // 选择框已变为Shanghai,注意注意

    console.log(textarea.val()); // 'Hello'
    textarea.val('Hi'); // 文本区域已更新为'Hi'
</script>

一个val()就统一了各种输入框的取值和赋值的问题

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

要删除DOM节点,拿到jQuery对象后直接调用remove()方法就可以了.如果jQuery对象包含若干DOM节点,实际上可以一次删除多个DOM节点:
var li = $('#test-div>ul>li');
li.remove(); // 所有<li>全被删除

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

jQuery提供show()和hide()方法,我们不用关心它是如何修改display属性的,总之它能正常工作:
var a = $('a[target=_self]');
a.hide(); // 隐藏
a.show(500); // 显示
a.toggle();   //根据当前状态决定是show()还是hide()
隐藏DOM节点并未改变DOM树的结构,只影响DOM节点的显示.和删除DOM节点是不同
类似的还有fadeIn() fadeOut() fadeToggle()

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

attr()和removeAttr()方法用于操作DOM节点的属性:
// <div id="test-div" name="Test" start="1">...</div>
var div = $('#test-div');
div.attr('data'); // undefined, 属性不存在
div.attr('name'); // 'Test'
div.attr('name', 'Hello'); // div的name属性变为'Hello'
div.removeAttr('name'); // 删除name属性
div.attr('name'); // undefined

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

批量获取/更改 ：
<div id='1'>1</div>
<div id='2'>2</div>
<div id='3'>3</div>
<button>Click Me</button>

<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<script>
$(function(){

        $('button').click(function() {
            for(let i of $('[id]'))   //此时i不是jQuery对象$(i)才是jQuery对象
            {
              //i.property只能修改已有属性的值
              switch(i.id){     
              //switch($(i).attr('id')){
                case '1':
                $(i).html('first');
                break;
                case '2':
                $(i).html('second');
                break;
                default:
                $(i).html('others');
              }           
            }
        });


    // $('button').click(function() {
    //     $('[id]').each(function(index){
    //         let tmp;
    //         switch(index)
    //         {
    //          case 0:
    //            tmp= 'first';
    //            break;
    //          case 1:
    //            tmp= 'second';
    //            break;
    //          default:
    //            tmp='others';
    //         }
    //         $(this).html(tmp);
    //     });
    // });

});
</script>

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

jQuery对象的text()和html()方法分别获取(第一个)/(批量)更改节点的文本和原始HTML文本(加html片段用append)

<ul id="test-ul">
    <li class="js">JavaScript</li>
    <li name="book">Java &amp; JavaScript</li>
</ul>
<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<script>
$(function(){
    alert($('#test-ul li[name=book]').text());     // 'Java & JavaScript'
    alert($('#test-ul li[name=book]').html());     // 'Java &amp; JavaScript'
    var j1 = $('#test-ul li.js');
    var j2 = $('#test-ul li[name=book]');
    j1.html('<span style="color: red">JavaScript</span>');
    j2.text('JavaScript & ECMAScript');
});
</script>

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

当判断checked,selected等属性时处理最好用is
<input id="test-radio" type="radio" name="test" checked value="1">
var radio = $('#test-radio');
radio.is(':checked'); // true

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

选择器: 
按ID查找
var div = $('#abc');   // 查找<div id="abc">,
如果id为abc的<div>存在,返回的jQuery对象就是[<div id="abc">...</div>],找不到就返回[]

按tag查找
var ps = $('p'); // 返回所有<p>节点
ps.length; // 数一数页面有多少个<p>节点

按class查找
var a = $('.red'); // 所有节点包含`class="red"`都将返回
var a = $('.red.green'); // 注意没有空格,查找同时包含red和green的节点<div class="red green">...</div>和<div class="blue green red">...</div>会被选中
var tr = $('tr.red'); // 找出<tr class="red ...">...</tr>

按属性查找
var email = $('[name=email]'); // 找出<name="email">
var passwordInput = $('[type=password]'); // 找出<type="password">
var a = $('[items="A B"]'); // 找出<items="A B">  当属性的值包含空格等特殊字符时，需要用双引号括起来
var emailInput = $('input[name=email]'); // 不会找出<div name="email">
var icons = $('[name^=icon]'); // 找出所有name属性值以icon开头的DOM// 例如: name="icon-1", name="icon-2"
var names = $('[name$=with]'); // 找出所有name属性值以with结尾的DOM// 例如: name="startswith", name="endswith"

多项选择器(多个选择器组合)
$('p,div');          // 把<p>和<div>都选出来
$('p.red,p.green'); // 把<p class="red">和<p class="green">都选出来
选出来的元素是按照它们在HTML中出现的顺序排列的,而且不会有重复元素.例如<p class="red green">不会被上面的$('p.red,p.green')选择两次

层级选择器(Descendant Selector),如果两个DOM元素具有层级关系,就可以用$('ancestor descendant')来选择,层级之间用空格隔开:
<div class="testing">
    <ul class="lang">
        <li class="lang-javascript">JavaScript</li>
        <li class="lang-python">Python</li>
        <li class="lang-lua">Lua</li>
    </ul>
</div>
选出JavaScript:
$('ul.lang li.lang-javascript');     // [<li class="lang-javascript">JavaScript</li>]
$('div.testing li.lang-javascript'); // [<li class="lang-javascript">JavaScript</li>]
选出所有的<li>节点:
$('ul.lang li');
这种层级选择器相比单个的选择器好处在于,它缩小了选择范围,避免了页面其他不相关的元素:
$('form[name=upload] input');    // 选择范围限定在name属性为upload的表单里
多层选择:
$('form.test p input'); // 在form表单选择被<p>包含的<input>

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

当拿到一个jQuery对象后,还可以以这个对象为基准进行查找和过滤
最常见的查找是在某个节点的所有子节点中查找,使用find()方法,它本身又接收一个任意的jQuery对象,返回的也是jQuery对象:
<ul class="lang">
    <li class="js dy">JavaScript</li>
    <li class="dy">Python</li>
    <li id="swift">Swift</li>
    <li class="dy">Scheme</li>
    <li name="haskell">Haskell</li>
</ul>

//节点内查找
var ul = $('ul.lang'); // 获得<ul>
var dy = ul.find('.dy'); // 获得JavaScript, Python, Scheme
var swf = ul.find('#swift'); // 获得Swift
var hsk = ul.find('[name=haskell]'); // 获得Haskell

//节点往上查找
var swf = $('#swift'); // 获得Swift
var parent = swf.parent(); // 获得Swift的上层节点<ul>
var parents = swf.parents(); // 获得Swift的所有父节点
var a = swf.parent('div.red'); // 从Swift的父节点开始向上查找,直到找到某个符合条件的节点并返回

//同一层级节点操作
var swift = $('#swift');
swift.next(); // Scheme
swift.siblings(); // Javascript,Python,Schema,Haskell
swift.next('[name=haskell]'); // Haskell,因为Haskell是后续第一个符合选择器条件的节点
swift.prev(); // Python
swift.prev('.js'); // JavaScript,因为JavaScript是往前第一个符合选择器条件的节点

//eq()方法返回被选元素中带有指定索引号的元素,索引号从0开始
$('li').eq(1)        //获得Python,支持负数索引,类似的还有first(),last()
$($('li')[1])        //等价于$('li').eq(1),相当于把$对象转换成DOM对象,然后再转换成$对象,但不支持负数索引
$($('li').get(-4))   //等价于$('li').eq(1),支持负数索引


