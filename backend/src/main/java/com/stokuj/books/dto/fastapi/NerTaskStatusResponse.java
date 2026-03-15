package com.stokuj.books.dto.fastapi;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.stokuj.books.model.fastapi.NerResult;

public record NerTaskStatusResponse(
        @JsonProperty("task_id") String taskId,
        String state,
        boolean ready,
        NerResult result,
        String error
) {}

