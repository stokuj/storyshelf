package com.stokuj.books.dto.fastapi;

import com.fasterxml.jackson.annotation.JsonProperty;

public record NerTaskResponse(
        @JsonProperty("task_id") String taskId
) {}

