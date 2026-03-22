package com.stokuj.books.dto.integration;

import java.util.List;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class BookFindPairsResult {

    private List<PairResult> pairs;
}
