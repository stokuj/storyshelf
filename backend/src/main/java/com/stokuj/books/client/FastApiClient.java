package com.stokuj.books.client;

import com.stokuj.books.dto.fastapi.AnalyseResponse;
import com.stokuj.books.dto.fastapi.AnalyseStats;
import com.stokuj.books.dto.fastapi.NerTaskResponse;
import com.stokuj.books.dto.fastapi.NerTaskStatusResponse;
import com.stokuj.books.model.fastapi.FindPairsResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Map;

@Slf4j
@Service
public class FastApiClient {

    private final WebClient client;

    public FastApiClient(WebClient storyweaveWebClient) {
        this.client = storyweaveWebClient;
    }

    public AnalyseStats analyse(String content) {
        return client.post()
                .uri("/analyse/")
                .bodyValue(Map.of("content", content))
                .retrieve()
                .onStatus(HttpStatusCode::isError, response ->
                        response.bodyToMono(String.class)
                                .doOnNext(body -> log.warn("Storyweave error {}: {}", response.statusCode(), body))
                                .then(Mono.error(new RuntimeException("Storyweave error: " + response.statusCode())))
                )
                .bodyToMono(AnalyseResponse.class)
                .map(AnalyseResponse::analysis)
                .block();
    }

    public String startNer(String content) {
        return client.post()
                .uri("/ner/")
                .bodyValue(Map.of("content", content))
                .retrieve()
                .onStatus(HttpStatusCode::isError, response ->
                        response.bodyToMono(String.class)
                                .doOnNext(body -> log.warn("Storyweave NER start error {}: {}", response.statusCode(), body))
                                .then(Mono.error(new RuntimeException("Storyweave NER error: " + response.statusCode())))
                )
                .bodyToMono(NerTaskResponse.class)
                .map(NerTaskResponse::taskId)
                .block();
    }

    public NerTaskStatusResponse pollNer(String taskId) {
        return client.get()
                .uri("/ner/{taskId}", taskId)
                .retrieve()
                .onStatus(HttpStatusCode::isError, response ->
                        response.bodyToMono(String.class)
                                .doOnNext(body -> log.warn("Storyweave NER poll error {}: {}", response.statusCode(), body))
                                .then(Mono.error(new RuntimeException("Storyweave NER poll error: " + response.statusCode())))
                )
                .bodyToMono(NerTaskStatusResponse.class)
                .block();
    }

    public FindPairsResult findPairs(String content, Iterable<String> names) {
        return client.post()
                .uri("/find-pairs/")
                .bodyValue(Map.of(
                        "content", content,
                        "names", names
                ))
                .retrieve()
                .onStatus(HttpStatusCode::isError, response ->
                        response.bodyToMono(String.class)
                                .doOnNext(body -> log.warn("Storyweave find-pairs error {}: {}", response.statusCode(), body))
                                .then(Mono.error(new RuntimeException("Storyweave find-pairs error: " + response.statusCode())))
                )
                .bodyToMono(FindPairsResult.class)
                .block();
    }

}
