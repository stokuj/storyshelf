package com.stokuj.books.model.fastapi;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class FindPairsResult {
    private List<CharacterPair> pairs;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CharacterPair {
        private List<String> pair;
        private List<String> sentences;
    }
}
