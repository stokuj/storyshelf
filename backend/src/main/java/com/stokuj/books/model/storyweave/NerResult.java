package com.stokuj.books.model.storyweave;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class NerResult {
    /**
     * Represents TODO
     */
    private String engine;
    private String modelName;
    private Map<String, Integer> characters;
    private Map<String, Integer> organizations;
    private Map<String, Integer> locations;
    private Map<String, Integer> miscellaneous;
    private double executionTimeSeconds;
}
