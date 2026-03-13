package com.stokuj.books.converter;

import tools.jackson.databind.ObjectMapper;
import com.stokuj.books.model.NerResult;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

@Converter
public class NerResultConverter implements AttributeConverter<NerResult, String> {
    /**
     * Converts TODO
     */
    private static final ObjectMapper mapper = new ObjectMapper();

    @Override
    public String convertToDatabaseColumn(NerResult nerResult) {
        try { return nerResult == null ? null : mapper.writeValueAsString(nerResult); }
        catch (Exception e) { throw new RuntimeException("NerResult serialize error", e); }
    }

    @Override
    public NerResult convertToEntityAttribute(String json) {
        try { return json == null ? null : mapper.readValue(json, NerResult.class); }
        catch (Exception e) { throw new RuntimeException("NerResult deserialize error", e); }
    }
}
