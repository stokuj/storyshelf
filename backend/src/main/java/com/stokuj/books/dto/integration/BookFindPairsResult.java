package com.stokuj.books.dto.integration;

import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class BookFindPairsResult {
    private List<CharacterPair> pairs;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CharacterPair {
        private List<String> pair;
        private List<String> sentences;
    }
}
