package com.stokuj.books.dto.integration;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AnalyseStats(
        @JsonProperty("char_count") int charCount,
        @JsonProperty("char_count_clean") int charCountClean,
        @JsonProperty("word_count") int wordCount,
        @JsonProperty("token_count") int tokenCount
) {}
