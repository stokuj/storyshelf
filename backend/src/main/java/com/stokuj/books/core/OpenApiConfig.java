package com.stokuj.books.core;

import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import org.springdoc.core.models.GroupedOpenApi;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@io.swagger.v3.oas.annotations.OpenAPIDefinition(info = @Info(title = "SpringShelf API", version = "v1"))
@SecurityScheme(
        name = "sessionAuth",
        type = SecuritySchemeType.APIKEY,
        in = io.swagger.v3.oas.annotations.enums.SecuritySchemeIn.COOKIE,
        paramName = "JSESSIONID"
)
public class OpenApiConfig {

    @Bean
    public GroupedOpenApi guestApi() {
        return GroupedOpenApi.builder()
                .group("1-guest-api")
                .displayName("1. Guest API (Public)")
                .pathsToMatch("/api/**")
                .pathsToExclude("/api/moderator/**", "/api/fastapi/**")
                .addOpenApiMethodFilter(method ->
                        !method.isAnnotationPresent(PreAuthorize.class)
                                && !method.getDeclaringClass().isAnnotationPresent(PreAuthorize.class))
                .build();
    }

    @Bean
    public GroupedOpenApi userApi() {
        return GroupedOpenApi.builder()
                .group("2-user-api")
                .displayName("2. User API (Authenticated)")
                .pathsToMatch("/api/**")
                .pathsToExclude("/api/moderator/**", "/api/fastapi/**")
                .addOpenApiMethodFilter(method ->
                        method.isAnnotationPresent(PreAuthorize.class)
                                || method.getDeclaringClass().isAnnotationPresent(PreAuthorize.class))
                .build();
    }

    @Bean
    public GroupedOpenApi moderatorApi() {
        return GroupedOpenApi.builder()
                .group("3-moderator-api")
                .displayName("3. Moderator API")
                .pathsToMatch("/api/moderator/**")
                .build();
    }

    @Bean
    public GroupedOpenApi integrationApi() {
        return GroupedOpenApi.builder()
                .group("4-integration-api")
                .displayName("4. Integration API (FastAPI)")
                .pathsToMatch("/api/fastapi/**")
                .build();
    }
}
