package com.stokuj.books.dto.integration;

import java.util.Map;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class NerResult {

    private Map<String, Integer> characters;
}
