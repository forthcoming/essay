package com.kugou.test;

import com.alibaba.druid.pool.DruidDataSourceFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;

import javax.sql.DataSource;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.InputStream;
import java.lang.reflect.Method;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Predicate;
import java.util.stream.Stream;

public class Main {

    public static void main(String[] args) throws Exception {   // 接收来自java命令的参数，默认以空格分开
        String encodedString = Base64.getEncoder().encodeToString("buster?java8".getBytes("utf-8"));
        byte[] decodedBytes = Base64.getDecoder().decode(encodedString);
        System.out.println("Base64编码字符串: " + encodedString);
        System.out.println("原始字符串: " + new String(decodedBytes, "utf-8"));

        Integer aa = Integer.valueOf("12");
        String bb = String.valueOf(23);
        Double cc = Double.valueOf("23.4");

        String[] split = "0,1,2,3".split(",",3);  // 意思是最多只要3个,第二个参数与python不同
        for(String s:split){
            System.out.println(s);
        }
        String s = String.format("name=%s, age=%d, score=%f","joe",23,2.2);  // 格式化字符串,一定要与后面的数据类型一致
        System.out.println(s);

        Objects.requireNonNull(2,"不能为空");

//        testThread();
//        testJedis();
//        testMysql();
//        testMysqlPool();
//        testJdbcTemplate();
        testAnnotation();
//        testPolymorphic();
//        testFunctionInterface();
    }

    static void eval(List<Integer> list, Predicate<Integer> predicate) {
        for(Integer n: list) {
            if(predicate.test(n)) {
                System.out.println(n + " ");
            }
        }
    }

    static void testFunctionInterface(){
        List<Integer> myList = List.of(1, 2, 3, 4, 5,6,7);   // of产生的list不能被修改(Immutable),只适用于List接口，Set接口，Map接口，不适用于接口的实现类

        // Predicate<Integer> predicate = n -> true
        // n 是一个参数传递到 Predicate 接口的 test 方法
        // n 如果存在则 test 方法返回 true
        System.out.println("输出所有数据:");
        eval(myList, n->true);

        // Predicate<Integer> predicate1 = n -> n%2 == 0
        // n 是一个参数传递到 Predicate 接口的 test 方法
        // 如果 n%2 为 0 test 方法返回 true
        System.out.println("输出所有偶数:");
        eval(myList, n-> n%2 == 0);

        System.out.println("stream使用:");
        // skip,limit有序，要注意
        // forEach无返回值,属于终结函数
        myList.stream().filter(nb->nb>2).filter(nb->(nb&1)==1).limit(2).skip(1).map(nb->String.valueOf(nb*2)).forEach(System.out::println);
        Stream<Integer> stream = Stream.of(1,2,3,4);  // 另一种获取流的方法
        System.out.println("11111111");
    }

    static void testThread() throws InterruptedException {
        //     java.util.concurrent.Executors是线程池的工厂类,用来生成线程池
        ExecutorService es = Executors.newFixedThreadPool(2);  // 创建固定数量的线程池
        es.submit(new RunnableImpl());
        es.submit(new RunnableImpl());
        es.submit(new RunnableImpl());
        es.submit(new RunnableImpl());
        es.shutdown();

        Thread t = new Thread(new RunnableImpl());
        t.setDaemon(true);  // 性质跟python一样
        t.start();
        t.join();
        new Thread(()->System.out.println("in RunableImpl "+Thread.currentThread().getName())).start();   // lambda表达式
    }

    static void testAnnotation() throws Exception{
        Class<Dog> dogClass = Dog.class;
        MyAnnotation annotation = dogClass.getAnnotation(MyAnnotation.class);
        /*
         * public class MyAnnotationImpl implements MyAnnotation{
         *     public int show1(){
         *         return 2;
         *     };
         *
         *     public String show2(){
         *         return "avatar";
         *     };
         * */
        if(annotation !=null){   // 注意要判断
            int show1 = annotation.show1();
            String show2 = annotation.show2();
            System.out.println(String.format("show1 = %d, show2 = %s",show1,show2));
        }
        Dog dog = new Dog("puppy");
        Class dogClassV1 = dog.getClass();  // 就是Dog.class
        Method[] methods = dogClass.getMethods();
        BufferedWriter bw = new BufferedWriter(new FileWriter("bug.txt"));
        for(Method method:methods){
            if(method.isAnnotationPresent(MyAnnotation.class)){
                System.out.println("被装饰的public方法名: "+method.getName());
                MyAnnotation methodAnnotation = method.getAnnotation(MyAnnotation.class);
                System.out.println(String.format("in method, show1 = %d, show2 = %s",methodAnnotation.show1(),methodAnnotation.show2()));
                try{
                    method.invoke(dog);
                } catch (Exception e) {
                    e.printStackTrace();
                    bw.write(method.getName()+" 方法出现异常\n");
                    bw.write("异常信息: "+e.toString()+"\n");
                }
            }
        }
        bw.flush();
        bw.close();
    }

    static void testException(){
        // 如果没有捕获异常,则需要在函数声明末尾抛出该异常(throws Exception)
        // 如果抛出的多个异常中存在父子关系,则只需要抛出父异常即可
        CheckingAccount account = new CheckingAccount();
        try {
            Thread.sleep(1000);   // 休眠3秒,当前线程进入停滞状态（阻塞当前线程），让出CPU的使用
            account.uncheckwithdraw(22);  // 非必须，可以不对非检查型异常进行捕获
            account.withdraw(22);  // 函数内部有检查性异常,所以这里必须手动捕获异常
        }catch(checkException e){
            System.out.println("checkException found, you are short $" + e.getAmount());
            e.printStackTrace();
        } catch(uncheckException e){
            System.out.println("uncheckException found, you are short $" + e.getAmount());
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } catch(Exception e) {
            System.out.println("Got an exception!"+e);
        } finally{
            System.out.println("in finally !,一定会执行");
        }
    }

    static void testGeneric(){
        Template template = new Template(6);  // 注意kugou.Dog访问权限要是public才行
        template.printArray(new Integer[]{1, 2, 3});
        template.printArray(new Character[]{'a','b','c'});

        ArrayList<Integer> list1=new ArrayList<>();
        list1.add(1);
        list1.add(2);
        ArrayList<String> list2=new ArrayList<>();
        list2.add("avatar");
        list2.add("hello");
        template.print(list1);
        template.print(list2);

        Template.Box<Integer> integerBox = new Template.Box<>();
        Template.Box<String> stringBox = new Template.Box<>();
        integerBox.add(10);
        stringBox.add("菜鸟教程");
        System.out.printf("整型值为 :%d\n", integerBox.get());
        System.out.printf("字符串为 :%s\n", stringBox.get());
    }

    static void testJedis() {
        Jedis jedis = new Jedis("localhost",2345);
        jedis.set("name","oracle");
        System.out.println(jedis.get("name"));
        jedis.close();

        // redis连接池
        JedisPool redisPool = new JedisPool();
        Jedis jpool = redisPool.getResource();
        jpool.set("age","12");
        jpool.close();  // 归还连接到连接池
    }

    static void testMysql() throws Exception {
        Connection conn =  DriverManager.getConnection("jdbc:mysql://localhost:3306/test?serverTimezone=UTC","root","root");
        conn.setAutoCommit(false);  // 关闭自动提交就是开启事物
        PreparedStatement stmt = conn.prepareStatement("select connection_id() as connection_id;"); // 防止SQL注入,参数用?占位符
//        stmt.executeUpdate();  // 执行DML(insert update delete),返回值是影响的行数
//        stmt.executeQuery();   // 执行DQL(select),返回类型是ResultSet
//        stmt.setString(1,username);  // 给占位符设置值,非必须
        ResultSet result = stmt.executeQuery();
        while (result.next()){
            System.out.println(result.getInt("connection_id"));
        }
        stmt.executeQuery("select sleep(20)");  // 方便观察
//        conn.rollback();
        conn.commit();
        stmt.close();
        conn.close();
    }

    static void testMysqlPool() throws Exception {
        Properties pro = new Properties();
        InputStream is = Main.class.getClassLoader().getResourceAsStream("druid.properties");
        pro.load(is);
        System.out.println(pro.getProperty("url"));
        DataSource ds = DruidDataSourceFactory.createDataSource(pro);
        Connection conn = ds.getConnection();
        System.out.println(conn);
        PreparedStatement stmt = conn.prepareStatement("select connection_id() as connection_id;");
        ResultSet result = stmt.executeQuery();
        while (result.next()){
            System.out.println(result.getInt("connection_id"));
        }
        stmt.executeQuery("select sleep(10)");  // 方便观察
        stmt.close();
        conn.close();
    }

    static void testJdbcTemplate() throws Exception {
        Properties pro = new Properties();
        InputStream is = Main.class.getClassLoader().getResourceAsStream("druid.properties");
        pro.load(is);
        DataSource ds = DruidDataSourceFactory.createDataSource(pro);
        JdbcTemplate template = new JdbcTemplate(ds);  // 自动释放资源,归还连接
        String sql = "select connection_id() as connection_id limit ?";
        List<Map<String, Object>> list = template.queryForList(sql,1);
        Integer connectionId = template.queryForObject(sql,Integer.class,1);
        System.out.println(list);
        System.out.println(connectionId);
        // update 执行DML操作(增删改)
        // queryForMap 查询结果封装为map集合,只能查一条数据
        // queryForList 查询结果封装为list集合,相当于由queryForMap组成的数组
        // queryForObject 查询结果封装为Object对象,一般用于执行聚合函数
        // query 查询结果封装为JavaBean对象,参数RowMapper一般用BeanPropertyRowMapper，用法: https://www.bilibili.com/video/BV1uJ411k7wy?p=568
    }

    static void testBasic(){
        Object obj = "string";
        if(obj instanceof String){
            ((String) obj).split("2");
        }

        System.out.println("char二进制位数：" + Character.SIZE);
        System.out.println("Character.MIN_VALUE="  + (int) Character.MIN_VALUE);
        System.out.println("Character.MAX_VALUE="  + (int) Character.MAX_VALUE);

        int integer =128;
        byte _integer = (byte)integer;    // 把容量大的类型转换为容量小的类型时必须使用强制类型转换
        System.out.println("_integer:"  + _integer);  // -128,溢出

        char character = 'a';   // 局部变量没有默认值，必须经过初始化，才可以使用
        int _character = character;
        System.out.println("_character:"  + _character);  // 97

        System.out.println( (int)-45.89 == -45);  // true,浮点数到整数的转换是通过舍弃小数得到，不是四舍五入

        System.out.println("4 >> 1 = "+(4>>1));          // 2
        System.out.println("-4 >> 1 = "+(-4>>1));       // -2
        System.out.println("-4 >>> 1 = "+(-4>>>1));  // 2147483646   => 01111111 11111111 11111111 11111110
        //        >> 带符号右移, 正数右移高位补0, 负数右移高位补1
        //        >>> 无符号右移, 无论是正数还是负数高位通通补0(对于正数而言>>和>>>没区别)

        Integer a=128;  // 如果数字范围在[-128,127]之间，相当于Integer a= Integer.valueOf(i), 会从缓存拿,相等,否则Integer a=new Integer(i),不相等
        Integer y=128;  // 对象比较要用equals
        System.out.println( "a==y: "+(a==y )+"\ta.equals(y): "+a.equals(y)+"\n");
        // 如果一个是int,一个是Integer,则会先转换为int,所以可以直接运算符对比
    }

    static void testPower(){
        Dog puppy = new Dog("puppy");
        System.out.println(puppy.public_value);
        System.out.println(puppy.protected_value);
        System.out.println(puppy.default_value);
        //  System.out.println(puppy.private_value);
        puppy.public_function();
        puppy.protected_function();
        puppy.default_function();
        //  puppy.private_function();

        System.out.println("doggy.sum(1,2,3,4)=" +  puppy.sum(1,2,3,4));
    }

    static void testArray(){
        int[][] dimensionNumbers = new int[2][3];  //多维数组
        char[] helloArray = { 'r', 'u', 'n', 'o', 'o', 'b'};
        String helloString = new String(helloArray);  //不可变对象
        String[] helloString1 = new String[10];    // 创建数组并将数组的引用赋值给变量helloString1
        int[] numbers = {10, 20, 30, 40, 50};  // 在堆内存区申请数组,然后将地址赋值给栈区变量
        int[] _numbers = numbers;    // 指向同一个堆内存地址
        System.out.println("numbers: "+numbers);
        for(int x : numbers ){
            System.out.print( x+"\n" );
        }
        String [] names ={"James", "Larry", "Tom", "Lacy"};
        for( String name : names ) {
            System.out.print( name+"\n" );
        }
    }

    static void testPolymorphic(){
        Animal animal = new Cat();
        System.out.println("animal.num = "+animal.num);  // 父类
        System.out.println("animal.age = "+animal.age);  // 父类
        animal.eat();   // 子类
        animal.sleep(); // 父类
        animal.run();   // 父类
//        System.out.println("animal.name = "+animal.name);   // 访问不到
//        animal.catchMouse();                                // 访问不到
//        总结:
//        成员变量: 编译看左边(父类),运行看左边(父类)
//        成员方法: 编译看左边(父类)，运行看右边(子类)。动态绑定
//        静态方法: 编译看左边(父类)，运行看左边(父类)。
//        (静态和类相关，算不上重写，所以，访问还是左边的)只有非静态的成员方法,编译看左边,运行看右边

        Cat cat = (Cat) animal;
        System.out.println("cat.num = "+cat.num);  // 子类
        System.out.println("cat.name = "+cat.name);  // 子类
        cat.eat(); // 子类
        cat.sleep(); // 子类
        cat.catchMouse(); // 子类
    }

    static void testStructure(){
//        LinkedHashSet<Integer> hashset = new LinkedHashSet<>();
//        HashSet<Integer> hashset = new HashSet<>();

//       LinkedList<Integer> linkedlist = new LinkedList<>();
        ArrayList<Integer> list = new ArrayList<>(); // 动态数组,范型只能是引用类型不能是基本类型
        Random r = new Random();
        for(int i=0;i<8;++i){
            list.add(r.nextInt(3)+1);  // 范围[1,3]
        }
        System.out.println(list);
        System.out.println(list.get(1));
        for(Integer __:list){
            System.out.println(__);
        }
//        for(Iterator<Integer> it = list.iterator();it.hasNext();){  // 等价写法
//            System.out.println(it.next());
//        }

        // LinkedHashMap<Integer,String> linkedhashmap = new LinkedHashMap<>();
        HashMap<Integer,String> hashmap = new HashMap<>();
        hashmap.put(1,"mysql");
        hashmap.put(1,"oracle");
        hashmap.put(2,"oracle");
        Set<Map.Entry<Integer, String>> entries = hashmap.entrySet();  // key-value
        for(Integer key: hashmap.keySet()){
            System.out.println("key is "+key+", value is "+hashmap.get(key));
        }
    }

}

class CheckingAccount {

    private double balance=12;

    public void withdraw(double amount) throws checkException {
        // 如果一个方法没有捕获到一个检查性异常,那么该方法必须使用throws关键字来声明,throws关键字放在方法签名的尾部
        if(amount <= balance) {
            balance -= amount;
        }else {
            double needs = amount - balance;
            throw new checkException(needs);
        }
    }

    public void uncheckwithdraw(double amount) {
        // 如果一个方法没有捕获到一个检查性异常,那么该方法必须使用throws关键字来声明,throws关键字放在方法签名的尾部
        if(amount <= balance) {
            balance -= amount;
        }else {
            double needs = amount - balance;
            throw new uncheckException(needs);
        }
    }
}

class uncheckException extends RuntimeException{  //自定义非检查性异常类
    private double amount;      //此处的amount用来储存当出现异常（取出钱多于余额时）所缺乏的钱
    public uncheckException(double amount){
        this.amount = amount;
    }
    public double getAmount(){
        return amount;
    }
}

class checkException extends Exception{  //自定义检查性异常类
    private double amount;      //此处的amount用来储存当出现异常（取出钱多于余额时）所缺乏的钱
    public checkException(double amount){
        this.amount = amount;
    }
    public double getAmount(){
        return amount;
    }
}

class RunnableImpl implements Runnable{

    @Override
    public void run(){
        System.out.println("in RunableImpl "+Thread.currentThread().getName());
        try {
            for(int i = 4; i > 0; i--) {
                System.out.println("Thread: " + i);
                Thread.sleep(50);
            }
        }catch (InterruptedException e) {
            System.out.println("Thread interrupted.");
        }
        System.out.println("Thread exiting.");
    }
}

// gradle build 打jar包
// java -jar xxx.jar 执行gradle打包的spring项目(./gradlew build)
// javap Dog.class  // 反编译
// Add as Library  // 添加驱动

// lambda表达式属于任何一个函数式接口类型
//默认方法就是接口可以有实现方法，而且不需要实现类去实现其方法。
//我们只需在方法名前面加个 default 关键字即可实现默认方法。

// 逻辑运算，条件判断都必须是Boolean类型
// Spring下载下来的都是jar包，需要加到classpath才能使用(File -> Project Structure -> Modules -> Dependencies)
// ==：基本类型比较的是数值大小,引用类型比较的是地址
// 对于复合数据类型（类），使用equals()和“==”效果是一样的

//可变参数（typeName... parameterName）
//传递同类型的可变参数给一个方法，java把可变参数当做数组处理
//一个方法中只能指定一个可变参数，它必须是方法的最后一个参数。任何普通的参数必须在它之前声明。

// 方法的参数是局部变量

// 反撤回ctrl y

//StringBuffer 和 StringBuilder 类的对象能够被多次的修改，并且不产生新的未使用对象。
//StringBuilder 类和 StringBuffer 之间的最大不同在于 StringBuilder 的方法不是线程安全的（不能同步访问）。
//由于 StringBuilder 相较于 StringBuffer 有速度优势，所以多数情况下建议使用 StringBuilder 类。然而在应用程序要求线程安全的情况下，则必须使用 StringBuffer 类。

// java的++和--规则跟c++一致
// java中逻辑运算符只返回true和false，这一点跟python不同
// variable x = (expression) ? value1( if true) : value2(if false)
// 循环包括while; do while;for
// 条件语句 if else if else; switch case

//内置数据类型
//byte：    1字节大小,范围[-2^7,2^7-1],默认值是0
//short：   2字节大小,范围[-2^15,2^15 - 1],默认值是0
//int：     4字节大小,范围[-2^31,2^31 - 1],默认值是0,整数默认为int类型
//long：    8字节大小,范围[-2^63,2^63 - 1],默认值是0L
//float：   4字节大小,默认值是0.0f
//double：  8字节大小,默认值是0.0d,浮点数默认为double类型
//boolean： 只有两个取值true和false,默认值false
//char：    2字节大小,Unicode字符,范围[\u0000,\uffff]

//整型、实型（常量）、字符型数据可以混合运算。运算中，不同类型的数据先转化为同一类型，然后进行运算。
//转换从低级到高级。
//低  ------------------------------------>  高
//byte,short,char—> int —> long—> float —> double


//编译
//javac Test.java
//运行
//java Test
//
//Java丢弃了C++中很少使用的、很难理解的、令人迷惑的那些特性，如操作符重载、多继承、自动的强制类型转换。特别地，Java语言不使用指针，而是引用。并提供了自动的废料收集
//
//一个源文件中只能有一个public类，可以有多个非public类，源文件的名称应该和public类的类名保持一致,所有java程序由public static void main(String []args)方法开始执行
//
// java注释 // 和 /* */
//
//局部变量：在方法、构造方法或者语句块中定义的变量被称为局部变量。没有默认值。变量声明和初始化都是在方法中，方法结束后，变量就会自动销毁。
//成员变量：成员变量是定义在类中，方法体之外的变量。有默认值，这种变量在创建对象的时候实例化。成员变量可以被类中方法、构造方法和特定类的语句块访问。
//类变量：类变量也声明在类中，方法体之外，但必须声明为static类型。
//
//JRE java运行时环境，包含了java虚拟机，java基础类库。是使用java语言编写的程序运行所需要的软件环境，是提供给想运行java程序的用户使用的。
//JDK java开发工具包，是程序员使用java语言编写java程序所需的开发工具包，是提供给程序员使用的。JDK包含了JRE，同时还包含了编译java源码的编译器javac

//因为“默认参数”和“方法重载”同时支持的话有二义性的问题，Java可能为了简单就不要“默认参数”了。
//使用“方法重载”可以间接实现”默认参数“的效果，而且避免了代码过于hack。

// @Override 重写 @Overload 重载
// 好处：增加可读性；编译器帮助检查错误