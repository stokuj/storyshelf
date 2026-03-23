package com.stokuj.books.integration.processor;

import com.stokuj.books.domain.entity.Book;
import com.stokuj.books.domain.entity.CharacterRelation;
import com.stokuj.books.dto.integration.BookFindPairsResult;
import com.stokuj.books.repository.CharacterRelationRepository;
import com.stokuj.books.service.CharacterService;
import com.stokuj.books.integration.kafka.ChapterEventProducer;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import com.stokuj.books.domain.entity.Character;

import java.util.List;
import java.util.Map;
import java.util.Objects;

@Component
public class RelationsResultProcessor {

    private final CharacterRelationRepository characterRelationRepository;
    private final CharacterService characterService;
    private final ChapterEventProducer chapterEventProducer;

    public RelationsResultProcessor(CharacterRelationRepository characterRelationRepository,
                                    CharacterService characterService,
                                    ChapterEventProducer chapterEventProducer) {
        this.characterRelationRepository = characterRelationRepository;
        this.characterService = characterService;
        this.chapterEventProducer = chapterEventProducer;
    }

    @Transactional
    public void processFindPairsResult(Book book, BookFindPairsResult result) {
        if (result.getPairs() != null) {
            result.getPairs().forEach(pairResult -> {
                List<String> pair = pairResult.getPair();
                if (pair == null || pair.size() < 2) {
                    return;
                }
                String sourceName = normalizeName(pair.get(0));
                String targetName = normalizeName(pair.get(1));
                if (sourceName == null || targetName == null) {
                    return;
                }
                Character source = characterService.findOrCreate(sourceName);
                Character target = characterService.findOrCreate(targetName);
                CharacterRelation relation = characterRelationRepository
                        .findByBookIdAndSourceIdAndTargetId(book.getId(), source.getId(), target.getId())
                        .orElse(null);
                if (relation == null) {
                    relation = new CharacterRelation();
                    relation.setBook(book);
                    relation.setSource(source);
                    relation.setTarget(target);
                    characterRelationRepository.save(relation);
                }
            });
        }

        if (result.getPairs() != null && !result.getPairs().isEmpty()) {
            chapterEventProducer.sendBookForRelations(book.getId(), result.getPairs());
        }
    }

    @Transactional
    public void processRelationsResult(Book book, Map<String, Object> result) {
        Object allRelations = result.get("all_relations");
        if (allRelations instanceof List<?> relationsList) {
            relationsList.stream()
                    .filter(item -> item instanceof Map<?, ?>)
                    .map(item -> (Map<?, ?>) item)
                    .forEach(item -> {
                        Object relationsObj = item.get("relations");
                        if (!(relationsObj instanceof Map<?, ?> relationsMap)) {
                            return;
                        }
                        Object innerRelations = relationsMap.get("relations");
                        if (!(innerRelations instanceof List<?> innerList)) {
                            return;
                        }
                        innerList.stream()
                                .filter(rel -> rel instanceof Map<?, ?>)
                                .map(rel -> (Map<?, ?>) rel)
                                .forEach(rel -> {
                                    String sourceName = normalizeName(asString(rel.get("source")));
                                    String targetName = normalizeName(asString(rel.get("target")));
                                    if (sourceName == null || targetName == null) {
                                        return;
                                    }
                                    Character source = characterService.findOrCreate(sourceName);
                                    Character target = characterService.findOrCreate(targetName);
                                    CharacterRelation relation = characterRelationRepository
                                            .findByBookIdAndSourceIdAndTargetId(book.getId(), source.getId(), target.getId())
                                            .orElseGet(() -> {
                                                CharacterRelation created = new CharacterRelation();
                                                created.setBook(book);
                                                created.setSource(source);
                                                created.setTarget(target);
                                                return created;
                                            });
                                    relation.setRelation(blankToNull(asString(rel.get("relation"))));
                                    relation.setEvidence(blankToNull(asString(rel.get("evidence"))));
                                    relation.setConfidence(asDouble(rel.get("confidence")));
                                    characterRelationRepository.save(relation);
                                });
                    });
        }
    }

    private String normalizeName(String name) {
        if (name == null) {
            return null;
        }
        String normalized = name.trim();
        return normalized.isEmpty() ? null : normalized;
    }

    private String asString(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof String text) {
            return text;
        }
        return Objects.toString(value, null);
    }

    private String blankToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }

    private Double asDouble(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        if (value instanceof String text) {
            String trimmed = text.trim();
            if (trimmed.isEmpty()) {
                return null;
            }
            try {
                return Double.parseDouble(trimmed);
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
    }
}
