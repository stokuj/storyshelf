package com.stokuj.books.dto.review;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ReviewRequest {

    private int rating;
    private String content;
}
