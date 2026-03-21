package com.stokuj.books.dto.fastapi;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class NerResult {
    /**
     * Represents TODO
     */
    private String engine;

    @JsonProperty("model_name")
    private String modelName;

    private Map<String, Integer> characters;
    private Map<String, Integer> organizations;
    private Map<String, Integer> locations;
    private Map<String, Integer> miscellaneous;

    @JsonProperty("execution_time_seconds")
    private double executionTimeSeconds;
}
