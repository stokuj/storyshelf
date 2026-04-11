package com.stokuj.books.integration.dto;

public record AnalyseStats(Integer charCount,
                           Integer charCountClean,
                           Integer wordCount,
                           Integer tokenCount) {
}
