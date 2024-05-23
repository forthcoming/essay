=>
箭头函数是匿名函数
(param1, param2, …, paramN) => { statements }
(param1, param2, …, paramN) => expression;        // equivalent to:  => { return expression; }
(...numbers)=>numbers.sort()              //rest参数用法

// 如果只有一个参数,圆括号是可选的:
(singleParam) => { statements }
singleParam => { statements }

// 无参数的函数需要使用圆括号:
() => { statements }

// 返回对象字面量时应当用圆括号将其包起来:
params => ({foo: bar})

JS每一个function有自己独立的运行上下文,而箭头函数不属于普通的function,所以没有独立的上下文
所以在箭头函数里写的this其实是包含该箭头函数最近的一个function上下文中的this(如果没有最近的function,就是全局)

/*******************************************************************************************************************************/

类型转换
// From anything to a number
let foo = "42";
let myNumber = Number(foo);

// Anything to string
let foo =42;
let myString= String(foo);

let a=2.33;
let myInt = Math.floor(a);  // ~~a通过位运算取整,只适用于32位

/*******************************************************************************************************************************/

let str=`
    if ( a )
        { 1+1; }
    else
        { 1+2; }
`;   // 多行字符串
let a = true;
let b = eval(str);  // returns 2
alert("b is : " + b);
a = false;
b = eval(str);  //returns 3,eval返回对最后一个表达式的求值结果
alert("b is : " + b);

eval("let test={a:1,b:'xx'}");  //字符串转换成对象,python中用test=eval("{'a':4,2:'a'}"),exec("test={'a':4,2:'a'}")

switch(action) {
    case 'draw':
        drawIt();
        break;
    case 'eat':
        eatIt();
        break;
    default:  //default语句是可选的
        doNothing();
}
//类似于c语言
//switch 和 case 都可以使用需要运算才能得到结果的表达式；在 switch 的表达式和 case 的表达式时使用 === 严格相等运算符进行比较

if{}
if{} else{}
if{} else if{} else{}
//类似于c语言

let x = 0;
for (let i=1; i<=10000; i++) {
    x += i;
} 
//类似于c语言

// JavaScript逻辑运算符&& || !
// Python中用的是and or not
// && || 返回的结果是决定表达式结果的值,not 返回false或者true,跟Python一致
let name = otherName || "default";

/*******************************************************************************************************************************/

立即执行一个刚定义好的匿名函数
(function(){do something...})()
//或
(function(){do something...}())

匿名函数后面的小括号()是为了让匿名函数立即执行,那大家有没有想过为什么这么写就会报错
function(){alert(1)}()

因为function前面没有(或者! ~之类的运算符,js解析器会试图将关键字function解析成函数声明语句，而不是函数定义表达式！
作为组运算符,小括号()会将其内部的表达式当成一个整体，然后返回结果，所以定义一个匿名函数正确的格式就是用小括号将函数体括起来！
同样的! ~ + -等运算符也有同样的效果，这是因为匿名函数也是一种值，这些运算符会将后面的函数体当成一个整体，先对匿名函数进行求值，然后在对结果进行运算！
不过这些运算符虽然能够达到让匿名函数立即执行的目的,但是要小心他们是有副作用的,比如:
!function() {return 1}()//false
~function() {return 1}()//-2
-function() {return false}()//0
-function() {return false}()//0
他们会对函数的返回值进行运算,这样可能会导致最终的结果和你想要的结果不一样

/*******************************************************************************************************************************/

Number
不区分整数和浮点数,统一用Number表示,以下都是合法的Number类型(Python中区分int,float,complex等)
123; // 整数123
0.456; // 浮点数0.456
1.2345e3; // 科学计数法表示1.2345x1000，等同于1234.5
-99; // 负数
NaN; // NaN表示Not a Number,当无法计算结果时用NaN表示
Infinity; // Infinity表示无限大,当数值超过了JavaScript的Number所能表示的最大值时,就表示为Infinity

JavaScript允许对任意数据类型做比较,有两种比较运算符:
第一种是==比较,它会自动转换数据类型再比较,很多时候,会得到非常诡异的结果
第二种是===比较,它不会自动转换数据类型,如果数据类型不一致返回false,如果一致再比较
由于JavaScript这个设计缺陷,不要使用==比较,始终坚持使用===比较,相应的不等用!==
false == 0; // true
false === 0; // false

NaN这个特殊的Number与所有其他值都不相等,包括它自己,唯一能判断NaN的方法是通过isNaN()函数
NaN === NaN; // false
isNaN(NaN); // true

浮点数的相等比较:因为计算机无法精确表示无限循环小数,要比较两个浮点数是否相等,只能计算它们之差的绝对值是否小于某个阈值
1 / 3 === (1 - 2 / 3); // false
Math.abs(1 / 3 - (1 - 2 / 3)) < 0.0000001; // true

/*******************************************************************************************************************************/

Boolean
布尔值只有true、false两种,可以直接用true、false表示布尔值,也可以通过布尔运算计算出来(Python中的bool类型用True和False)
JavaScript把null、undefined、0、NaN和空字符串''视为false,其他值一概视为true

/*******************************************************************************************************************************/

String
由于多行字符串用\n写起来比较费事,所以最新的ES6标准新增了一种多行字符串的表示方法,用` ... `表示
`这是一个
多行
字符串`;

要把多个字符串连接起来,可以用+号连接:
let name = '小明';
let age = 20;
let message = '你好, ' + name + ', 你今年' + age + '岁了!';
alert(message);   //你好, 小明, 你今年20岁了!
message.length;    //16

or

let name = '小明';
let age = 20;
let message= `你好, ${name}, 你今年${age}岁了!`;   //注意用的是``
alert(message);   //你好, 小明, 你今年20岁了!
let [a,b]=name;   //a='小',b='明'

/*******************************************************************************************************************************/

Set(值唯一,Python中的集合)
let s = new Set(['a', 'b', 'c']);
s.add('a').add('11');
s.delete('c');
s.has('c');  //false
s.size;  // 3
s.keys();  //SetIterator {"a", "b", "11"}
s.values(); //SetIterator {"a", "b", "11"}
for (let i of s){      // Set的遍历顺序就是插入顺序
    console.log(i)
};

/*******************************************************************************************************************************/

Map(Python中的字典结构)
let m = new Map([['Michael', 95], ['Bob', 75], [12, 85]]);
for (let [key, value] of m) {
    console.log(value); 
}

初始化Map需要一个二维数组,或者直接初始化一个空Map。Map具有以下方法
let m = new Map(); // 空Map
m.set('Adam', 67); // 添加新的key-value
m.set('Bob', 59);
m.size; //3
m.has('Adam'); // 是否存在key 'Adam': true
m.get('Adam'); // 67
m.delete('Adam'); // 删除key 'Adam'
m.get('Adam'); // undefined
m.keys();
m.values();

由于一个key只能对应一个value,所以多次对一个key放入value,后面的值会把前面的值冲掉
let m = new Map();
m.set('Adam', 67);
m.set('Adam', 88);
m.get('Adam'); // 88

/*******************************************************************************************************************************/

Array
let arr = [1, 2, 3.14, 'Hello', null, true];
arr.includes(4);   // false
for (let value of arr) {  
    console.log(value);  
}
for(let x of arr.keys()){
    console.log(x);   // 返回下标
}  // values()获得数组中所有元素的数据,entries()获得数组中所有数据的下标和数据

arr[0]; // 返回索引为0的元素,即1
arr[5]; // 返回索引为5的元素,即true
arr[6]; // 索引超出了范围,返回undefined
Array.isArray(arr)  //判断是不是数组(解构赋值)

let a=1,b=2;
[a,b]=[b,a];   //交换a,b的值
[a,,b]=[4,5,6];       //a=4,b=6
[a,...b]=[4,5,6]; //a=4,b=[5,6]
new Array(2).fill(0).concat([1,2,3]);    // [0,0,1,2,3]

如果通过索引赋值时索引超过了范围,同样会引起Array大小的变化
let arr = [1, 2, 3];
arr.filter(x=>x>2);  //[3]
arr[5] = 'x';  //编写代码时，不建议直接修改Array的大小
arr; // arr变为[1, 2, 3, undefined, undefined, 'x']

Array可以通过索引把对应的元素修改为新的值
let arr = ['A', 'B', 'C'];
arr[1] = 99;
arr; // arr现在变为['A', 99, 'C']

直接给Array的length赋一个新的值会导致Array大小的变化
let arr = [1, 2, 3];
arr.length; // 3
arr.length = 6;
arr; // arr变为[1, 2, 3, undefined, undefined, undefined]
arr.length = 2;
arr; // arr变为[1, 2]

与String类似,Array也可以通过indexOf()来搜索一个指定的元素的位置
let arr = [10, 20, '30', 'xyz'];
arr.indexOf(10); // 元素10的索引为0
arr.indexOf(20); // 元素20的索引为1
arr.indexOf(30); // 元素30没有找到,返回-1
arr.indexOf('30'); // 元素'30'的索引为2

push()向Array的末尾添加若干元素,pop()则把Array的最后一个元素删除掉
let arr = [1, 2];
arr.push('A', 'B'); // 返回Array新的长度: 4
arr; // [1, 2, 'A', 'B']
arr.pop(); // pop()返回'B'
arr; // [1, 2, 'A']
arr.pop();
arr.pop();
arr.pop(); // 连续pop 3次
arr; // []
arr.pop(); // 空数组继续pop不会报错，而是返回undefined
arr; // []

如果要往Array的头部添加若干元素,使用unshift()方法,shift()方法则把Array的第一个元素删掉
let arr = [1, 2];
arr.unshift('A', 'B'); // 返回Array新的长度: 4
arr; // ['A', 'B', 1, 2]
arr.shift(); // 'A'
arr; // ['B', 1, 2]
arr.shift();
arr.shift();
arr.shift(); // 连续shift3次
arr; // []
arr.shift(); // 空数组继续shift不会报错,而是返回undefined
arr; // []

slice()就是对应String的substring()版本,它截取Array的部分元素,然后返回一个新的Array
let arr = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];
arr.slice(0, 3); // 从索引0开始，到索引3结束，但不包括索引3: ['A', 'B', 'C']
arr.slice(3); // 从索引3开始到结束: ['D', 'E', 'F', 'G']

注意到slice()的起止参数包括开始索引,不包括结束索引
如果不给slice()传递任何参数，它就会从头到尾截取所有元素.利用这一点我们可以很容易地复制一个Array
let arr = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];
let aCopy = arr.slice();
aCopy; // ['A', 'B', 'C', 'D', 'E', 'F', 'G']
aCopy === arr; // false   因为Array是对象,==或===操作符只能比较两个对象是否是同一个实例,也就是是否是同一个对象引用

sort()可以对当前Array进行排序,它会直接修改当前Array的元素位置,直接调用时按照默认顺序排序
let arr = ['B', 'C', 'A'];
arr.sort();
arr; // ['A', 'B', 'C']

reverse()把整个Array的元素反转
let arr = ['one', 'two', 'three'];
arr.reverse(); 
arr; // ['three', 'two', 'one']

splice()方法是修改Array的"万能方法",它可以从指定的索引开始删除若干元素,然后再从该位置添加若干元素
let arr = ['Microsoft', 'Apple', 'Yahoo', 'AOL', 'Excite', 'Oracle'];
// 从索引2开始删除3个元素,然后再添加两个元素:
arr.splice(2, 3, 'Google', 'Facebook'); // 返回删除的元素 ['Yahoo', 'AOL', 'Excite']
arr; // ['Microsoft', 'Apple', 'Google', 'Facebook', 'Oracle']
// 只删除,不添加:
arr.splice(2, 2); // ['Google', 'Facebook']
arr; // ['Microsoft', 'Apple', 'Oracle']
// 只添加,不删除:
arr.splice(2, 0, 'Google', 'Facebook'); // 返回[],因为没有删除任何元素
arr; // ['Microsoft', 'Apple', 'Google', 'Facebook', 'Oracle']

let arr = ['A', 'B', 'C'];
let added = [4,...arr,5,...[1,2,3]];
added; // [4, "A", "B", "C", 5, 1, 2, 3]
arr; // ["A", "B", "C"]

join()把当前Array的每个元素都用指定的字符串(默认是',' )连接起来,然后返回连接后的字符串
let arr = ['A', 'B', 'C', 1, 2, 3];
arr.join('-'); // 'A-B-C-1-2-3'

如果Array的元素不是字符串,将自动转换为字符串后再连接
Python则不会自动转换
s=[1,2,4,[1,'45',],'qw',{2,5,'er'}]
print(('---').join((str(_) for _ in s)))    #返回 1---2---4---[1, '45']---qw---{2, 5, 'er'}

/*******************************************************************************************************************************/

indexOf() &  includes() &  startsWith() &  endsWith()
let s = 'hello, world';
s.indexOf('world'); // 7
s.indexOf('World'); // -1
s.includes('hel');   //true
s.startsWith('h');  //true
s.endsWith('y');  //false

/*******************************************************************************************************************************/

split()按指定字符拆分字符串成数组(跟python一致,只不过这里没有默认拆分空白符)
let s = 'hello,world';
s.split(','); // ["hello", "world"]

/*******************************************************************************************************************************/

substr()返回指定索引区间的子串(Python中用切片)
let s = 'hello, world'
s.substr(7); // 从索引7开始到结束，返回'world'
s.substr(-5,3); // 从索引5开始截取3个长度，返回'wor'

字符串是不可变的,如果对字符串的某个索引赋值,不会有任何错误,但是也没有任何效果
let s = 'Test';
s[0] = 'X';
alert(s);  // s仍然为'Test'

/*******************************************************************************************************************************/

let 用于定义变量,const 用于定义常量,都是块级作用域,其有效范围仅在代码块中,不允许重复声明
每个语句以;结束,语句块用{}
const arr=[1,2];  // arrs是常量,但指向的对象本身仍是可变对象
// let arr=1;    Uncaught SyntaxError: Identifier 'arr' has already been declared
arr[0]=3;
console.log(arr);   // [3, 2]
// arr='string';     Uncaught TypeError: Assignment to constant variable.

/*******************************************************************************************************************************/

耗时测试
console.time("timer");
for(let i of [1,2,3]){
    console.log(i);
}
console.timeEnd("timer");

/*******************************************************************************************************************************/

class
class Point {
    constructor(x, y) {
        this.x = x;
        this.y = y;
    }
    toString() {
        return '(' + this.x + ', ' + this.y + ')';
    }
}
p=new Point(1,2)

/*******************************************************************************************************************************/

//async关键字用于声明一个异步函数,返回一个Promise
//await关键字只能在async函数中使用,它会暂停执行async函数,直到await后面的Promise对象执行完成并返回结果,它使得我们能够以同步的方式写异步代码
//async函数本身会马上返回,不会阻塞当前线程,内部由await关键字修饰异步过程,会阻塞等待异步任务的完成再返回
//当Promise对象的状态变为fulfilled时会调用.then方法,状态为rejected时会调用.catch,状态为pending表示初始状态,既没有被兑现也没有被拒绝
//then和catch都返回Promise对象,都支持链式操作
//建议用await和try catch代替then和catch,但await只能在标记为async的函数内部使用,而then可以在任何地方使用
