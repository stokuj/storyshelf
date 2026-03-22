FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
#RUN mvn -q -DskipTests package

FROM eclipse-temurin:21-jre
LABEL authors="dv6"
RUN groupadd --system spring && useradd --system --gid spring spring
USER spring:spring
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
