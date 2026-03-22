package com.stokuj.books.dto.integration;

public record AnalyseStats(Integer charCount,
                           Integer charCountClean,
                           Integer wordCount,
                           Integer tokenCount) {
}
