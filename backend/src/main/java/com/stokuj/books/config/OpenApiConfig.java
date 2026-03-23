package com.stokuj.books.config;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import org.springdoc.core.models.GroupedOpenApi;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@OpenAPIDefinition(
        info = @Info(title = "SpringShelf API", version = "v1"),
        security = @SecurityRequirement(name = "bearerAuth")
)
@SecurityScheme(
        name = "bearerAuth",
        type = SecuritySchemeType.HTTP,
        scheme = "bearer",
        bearerFormat = "JWT"
)
public class OpenApiConfig {

    @Bean
    public GroupedOpenApi publicApi() {
        return GroupedOpenApi.builder()
                .group("1-public-api")
                .displayName("1. Public / User API")
                .pathsToMatch("/api/**")
                .pathsToExclude("/api/admin/**", "/api/fastapi/**")
                .build();
    }

    @Bean
    public GroupedOpenApi adminApi() {
        return GroupedOpenApi.builder()
                .group("2-admin-api")
                .displayName("2. Admin API")
                .pathsToMatch("/api/admin/**")
                .build();
    }

    @Bean
    public GroupedOpenApi integrationApi() {
        return GroupedOpenApi.builder()
                .group("3-integration-api")
                .displayName("3. Integration API (FastAPI)")
                .pathsToMatch("/api/fastapi/**")
                .build();
    }
}
