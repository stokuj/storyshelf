package com.stokuj.books.analysis;

import java.util.Map;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class NerResult {

    private Map<String, Integer> characters;
}
