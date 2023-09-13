package com.kugou.test;

import java.lang.annotation.*;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.Arrays;

/**
 * 注解javadoc演示(javadoc Dog.java)
 * @author zgt
 * @version 1.0
 * @since 1.5
 */
@MyAnnotation(show1 = 2,show2 = "avatar")
public class Dog {
    String breed; // 成员变量,默认值null,对子类可见
    int age; // 默认值0,仅在本类可见
    static int count; // 类变量,又叫静态变量
    Lock lock = new ReentrantLock();
    /*
     *  final修饰的变量是常量,无法修改
     *  父类中的 final 方法可以被子类继承，但是不能被子类重写,可以被重载
     *  final 类不能被继承，没有类能够继承 final 类的任何特性
     * */
    static final String TITLE = "Manager";

    /*
     *  public 对所有地方可见
     *  protected不同包子类可以访问
     *  default即包访问权限,在同一包内可见
     *  private 只能在本类内部可见
     * 权限大小 public > protected > default > private
     *  子类重写的方法的权限修饰符不小于父类被重写的方法的权限修饰符, private除外,应为无法继承到子类
     * */
    public int public_value=1;
    protected int protected_value=2;
    int default_value=3;
    private int private_value=4;

    @MyAnnotation(show1 = 1,show2 = "oracle")
    public void public_function(){
        System.out.println("in public_function");
    }

    protected void protected_function(){
        System.out.println("in protected_function");
    }
    void default_function(){
        System.out.println("in default_function");
    }
    private void private_function(){
        System.out.println("in private_function");
    }

    static {
        System.out.println("静态代码块执行");   // 静态代码块，当第一次用到本类时执行一次
    }
    public Dog(String breed, int _age) {
        this.breed = breed;
        age = _age;
        count += 1;
    }

    public Dog(String name) { // 构造方法的名称必须与类同名,一个类可以有多个构造方法,没有返回值类型
        System.out.println("小狗的名字是 : " + name);
    }

    /**
     * 注解javadoc演示
     * @param number 数组
     * @return  函数返回值
     */
    int sum(int... number){  // 此时number类型是int[]
        lock.lock();
        int amount =0;
        for(int _number:number){
            amount+=_number;
        }
        lock.unlock();
        return amount;
    }
}

class MyDog extends Dog implements MyInterface1,MyInterface2{
    public String color;

    public MyDog(String breed, int _age,String color) {
        /*
         * 接口不能直接实例变量
         * 我们可以通过super关键字来实现对父类成员的访问，用来引用当前对象的父类。
         * 子类是不继承父类的构造器，它只是调用（隐式或显式）。如果父类的构造器带有参数，则必须在子类的构造器中显式地通过 super 关键字调用父类的构造器并配以适当的参数列表。
         * 如果父类构造器没有参数，则在子类的构造器中不需要使用 super 关键字调用父类构造器，系统会自动调用父类的无参构造器。（super调用父类函数必须放在子类构造函数第一行）
         * */
        super(breed, _age);  // 父类不含默认构造函数,所以需要在第一行手动调用
        this.color = color;
    }

    @Override
    public void method(){
        System.out.println("类中实现接口方法");
    }

}

interface MyInterface1{
}

interface MyInterface2{
    void method();   // 省略了public abstract
}

class Person{
    String name;
    int age;

    Person(String name,int age){
        this.name = name;
        this.age = age;
    }

    @Override
    public String toString() {
        return "Person{" +
                "name='" + name + '\'' +
                ", age=" + age +
                '}';
    }
}

class testLambda {

    static void main() {
        Person[] arr = {
                new Person("柳岩",30),
                new Person("akatsuki",18),
                new Person("oracle",24),
        };
        Arrays.sort(arr,(p1,p2)->p2.age-p1.age);
        for(Person p:arr){
            System.out.println(p);
        }

        // 函数的返回值类型是函数式接口时,那么可以返回这个接口的匿名内部类或者lambda表达式
        // 函数的参数是一个接口且接口中仅有一个抽象方法(函数式接口),可以使用匿名内部类或者lambda表达式或者实现了接口的类实例
        invokeCalc(3,5,(x,y)->x+y);
        invokeCalc(3, 5, new Calculator() {
            @Override
            public int calc(int x, int y) {
                return x+y;
            }
        });

    }

    static Integer invokeCalc(int a,int b,Calculator calculator){
        int sum = calculator.calc(a,b);
        System.out.println("sum = "+sum);
        return sum;
    }
}

@FunctionalInterface   // 函数式接口
interface Calculator{
    int calc(int x, int y);
}


class Reflect{

    void testReflect() throws Exception {
        Class templateClass = Template.class;

        Field[] publicFields = templateClass.getFields();  // 只能获取所有public修饰的成员变量
        Field[] allFields = templateClass.getDeclaredFields();  // 获取所有成员变量
        for(Field field:allFields){
            System.out.println(field);
        }
        System.out.println(templateClass.getName());    // 获取类名
        Field field = templateClass.getDeclaredField("age");  // 利用反射修改私有变量
        field.setAccessible(true);  // 忽略访问权限修饰符检测
        Template template = new Template(6);
        System.out.println(field.get(template));
        field.set(template,22);
        System.out.println(template.getAge());

        Method method = templateClass.getMethod("testReflect", Integer.class);  // 获取指定名字的public描述符描述的方法
        method.setAccessible(true);
        method.invoke(template,4);

        Constructor constructor = templateClass.getConstructor(int.class);  // 获取构造函数
        constructor.setAccessible(true);
        System.out.println("constructor: "+constructor);
        Object newDog = constructor.newInstance(66);   // 构造Dog对象
    }
}


/*
元注解: 用于描述注解的注解
@Target      描述注解能够使用的位置
    ElementType
        TYPE: Class, interface (including annotation type), enum, or record declaration
        FIELD: Field declaration (includes enum constants)
        METHOD: Method declaration
@Retention   描述注解被保留的阶段
    RetentionPolicy
        SOURCE: Annotations are to be discarded by the compiler.@Override就是用的SOURCE,在编译期间会进行语法检查！编译器处理完后就没有任何作用了
        CLASS: Annotations are to be recorded in the class file by the compiler but need not be retained by the VM at run time. This is the default behavior.
        RUNTIME: Annotations are to be recorded in the class file by the compiler and retained by the VM at run time, so they may be read reflectively.see java.lang.reflect.AnnotatedElement
@Documented  描述注解是否被抽取到api文档中
@Inherited   描述注解是否被子类继承
*/
@Target({ElementType.METHOD,ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Documented
@interface MyAnnotation {  // 注解本质是接口
    int show1();
    String show2();
    double[] show3() default {};
    // 返回值可以是基本数据类型,String,枚举,注解,或以上类型的数组
}



