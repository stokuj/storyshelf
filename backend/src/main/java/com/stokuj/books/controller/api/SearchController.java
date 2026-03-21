package com.stokuj.books.controller.api;

import com.stokuj.books.model.entity.Book;
import com.stokuj.books.service.BookService;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class SearchController {

    private final BookService bookService;

    public SearchController(BookService bookService) {
        this.bookService = bookService;
    }

    @GetMapping("/api/search")
    public List<Book> search(@RequestParam(required = false) String q) {
        return bookService.search(q);
    }
}
