package com.stokuj.books;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class SpringShelfApplication {

    public static void main(String[] args) {

        SpringApplication.run(SpringShelfApplication.class, args);
    }

}
