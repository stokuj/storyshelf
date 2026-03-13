package com.stokuj.books.converter;

import com.stokuj.books.model.RelationsResult;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import tools.jackson.databind.ObjectMapper;

@Converter
public class RelationsResultConverter implements AttributeConverter<RelationsResult, String> {
    private static final ObjectMapper mapper = new ObjectMapper();

    @Override
    public String convertToDatabaseColumn(RelationsResult result) {
        try { return result == null ? null : mapper.writeValueAsString(result); }
        catch (Exception e) { throw new RuntimeException("RelationsResult serialize error", e); }
    }

    @Override
    public RelationsResult convertToEntityAttribute(String json) {
        try { return json == null ? null : mapper.readValue(json, RelationsResult.class); }
        catch (Exception e) { throw new RuntimeException("RelationsResult deserialize error", e); }
    }
}