package com.kugou.util;

import java.util.List;
import java.util.Map;

public class Injection {
    private Integer score;
    private Integer id;
    private String name;
    private boolean gender;
    private List<Object> list;
    private Map<String ,Object> map;

    public Injection(Integer score, String name) {
        System.out.println("2个参数构造函数");
        this.score = score;
        this.name = name;
    }

    public Injection(Integer score) {
        System.out.println("1个参数构造函数");
        this.score = score;
    }

    public Injection() {
        System.out.println("无参构造函数");
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public boolean isGender() {
        return gender;
    }

    public void setGender(boolean gender) {
        this.gender = gender;
    }

    public List<Object> getList() {
        return list;
    }

    public void setList(List<Object> list) {
        this.list = list;
    }

    public Map<String, Object> getMap() {
        return map;
    }

    public void setMap(Map<String, Object> map) {
        this.map = map;
    }

    public Integer getScore() {
        return score;
    }

    public void setScore(Integer score) {
        this.score = score;
    }

    @Override
    public String toString() {
        return "Injection{" +
                "score=" + score +
                ", id=" + id +
                ", name='" + name + '\'' +
                ", gender=" + gender +
                ", list=" + list +
                ", map=" + map +
                '}';
    }
}
