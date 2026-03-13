package com.stokuj.books.client;

import com.stokuj.books.dto.AnalyseResponse;
import com.stokuj.books.dto.AnalyseStats;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Map;

@Slf4j
@Service
public class StoryweaveClient {

    private final WebClient client;

    public StoryweaveClient(WebClient storyweaveWebClient) {
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
}
