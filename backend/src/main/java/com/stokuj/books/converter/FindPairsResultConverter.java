package com.stokuj.books.converter;

import com.stokuj.books.model.FindPairsResult;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import tools.jackson.databind.ObjectMapper;

@Converter
public class FindPairsResultConverter implements AttributeConverter<FindPairsResult, String> {
    private static final ObjectMapper mapper = new ObjectMapper();

    @Override
    public String convertToDatabaseColumn(FindPairsResult result) {
        try { return result == null ? null : mapper.writeValueAsString(result); }
        catch (Exception e) { throw new RuntimeException("FindPairsResult serialize error", e); }
    }

    @Override
    public FindPairsResult convertToEntityAttribute(String json) {
        try { return json == null ? null : mapper.readValue(json, FindPairsResult.class); }
        catch (Exception e) { throw new RuntimeException("FindPairsResult deserialize error", e); }
    }
}