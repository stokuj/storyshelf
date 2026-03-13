package com.stokuj.books.dto;

public record AnalyseStats(
        int charCount,
        int charCountClean,
        int wordCount,
        int tokenCount
) {}
