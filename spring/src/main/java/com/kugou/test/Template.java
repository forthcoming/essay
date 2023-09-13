package com.kugou.test;

import java.util.ArrayList;


public class Template{
    public String name="puppy";
    private int age = 12;

    public Template(int age){
        this.age = age;
    }

    public void testReflect(Integer value){
        System.out.println("in testReflect, value is "+value);
    }

    public void print(ArrayList<?> array){  // ?代表泛型通配符，仅参数传递可用,变量定义时不可用
        //    <? extend Number> 代表使用的泛型必须是Number类型的子类或者本身
        //    <? super Number> 代表使用的泛型必须是Number类型的父类或者本身
        for(Object item:array){
            System.out.println("print:item"+item);
        }
    }

    public <E> void printArray(E[] inputArray){  // 泛型方法，<E>是泛型方发声明，在方法返回类型之前
        for(E item:inputArray){
            System.out.println("printArray:item: "+item);
        }
    }

    public int getAge() {
        return age;
    }

    public static class Box<E> {   // 泛型类,泛型的本质是参数化类型,类名后面添加类型参数声明部分<E>
        private E t;

        public void add(E t) {
            this.t = t;
        }

        public E get() {
            return t;
        }
    }

}

