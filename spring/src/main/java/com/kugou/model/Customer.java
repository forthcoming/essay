package com.kugou.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnore;

import java.util.Date;

public class Customer{
    private long id;
    private String firstName,lastName;
    private int age=24;
    @JsonIgnore  // 序列化时忽略该字段
    private String password;
    @JsonFormat(pattern = "yyyy-MM-dd hh:mm:ss",locale = "zh",timezone = "GMT+8")
    private Date birthday;

    public Customer(long id,String firstName,String lastName,String password){
        this.id=id;
        this.firstName=firstName;
        this.lastName=lastName;
        this.password = password;
        this.birthday = new Date();  // 当前时间
    }

    public long getId() {
        return id;
    }

    public String getFirstName() {
        return firstName;
    }

    public String getLastName() {
        return lastName;
    }

    @Override
    public String toString() {
        return "Customer{" +
                "id=" + id +
                ", firstName='" + firstName + '\'' +
                ", lastName='" + lastName + '\'' +
                ", age=" + age +
                ", password='" + password + '\'' +
                ", birthday=" + birthday +
                '}';
    }
}
