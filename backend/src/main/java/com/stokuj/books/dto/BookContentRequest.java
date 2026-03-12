package com.stokuj.books.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class BookContentRequest {

    @NotBlank(message = "Treść nie może być pusta")
    private String content;
}
