package com.stokuj.books.model.fastapi;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class RelationsResult {
    private List<String> pair;
    private Integer sentencesCount;
    private String relations;
}
