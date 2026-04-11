package com.stokuj.books.integration.dto;

import java.util.List;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class BookFindPairsResult {

    private List<PairResult> pairs;
}
