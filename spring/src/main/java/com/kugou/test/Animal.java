package com.kugou.test;

public class Animal {
    int num=10;
    static int age=20;

    public void eat(){
        System.out.println("animal is eating");
    }

    public static void sleep(){
        System.out.println("animal is sleeping");
    }

    public void run(){
        System.out.println("animal is running");
    }
}

class Cat extends Animal{
    int num = 80;
    String name = "tomcat";

    @Override
    public void eat(){
        System.out.println("cat is eating");
    }

    public static void sleep(){
        System.out.println("cat is sleeping");
    }

    public void catchMouse(){
        System.out.println("cat is catching mouse");
    }
}
