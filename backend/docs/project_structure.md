com.stokuj.books/
├── SpringShelfApplication.java
├── analysis/
│   ├── dto/
│   │   ├── AnalyseResponse.java
│   │   ├── AnalyseStats.java
│   │   ├── BookFindPairsResult.java
│   │   ├── NerResult.java
│   │   └── PairResult.java
│   ├── kafka/
│   │   ├── AnalysisResultConsumer.java
│   │   └── ChapterEventProducer.java
│   └── processor/
│       ├── NerResultProcessor.java
│       └── RelationsResultProcessor.java
├── auth/
├── author/
├── book/
│   ├── book/
│   ├── chapter/
│   ├── character/
│   └── tag/
├── config/
│   ├── FlywayConfig.java
│   ├── KafkaConfig.java
│   └── OpenApiConfig.java
├── exception/
│   ├── ConflictException.java
│   ├── GlobalExceptionHandler.java
│   ├── ResourceNotFoundException.java
│   └── UnauthorizedException.java
├── review/
├── security/
│   ├── RoleConfig.java
│   ├── SecurityConfig.java
│   └── UserDetailsServiceImpl.java
├── series/
├── shelf/
└── user/

src/main/resources/
├── application-dev.yml
├── application.yml
├── db/
│   └── migration/
│       └── V1__init_schema.sql
└── templates/
    ├── layout/
    │   └── base.html
    ├── admin-book-form.html
    ├── admin-reviews.html
    ├── book.html
    ├── bookshelf.html
    ├── error.html
    ├── home.html
    ├── profile.html
    ├── register.html
    ├── login.html
    └── settings.html

src/test/java/
└── com/stokuj/books/
    ├── book/
    │   └── book/
    │       └── BookServiceTest.java
    ├── config/
    │   └── TestSecurityConfig.java
    └── controller/
        └── api/
            ├── admin/
            │   ├── AdminAuthorControllerIT.java
            │   ├── AdminBookControllerIT.java
            │   ├── AdminChapterControllerIT.java
            │   ├── AdminReviewControllerIT.java
            │   └── AdminSeriesControllerIT.java
            ├── user/
            │   ├── BookShelfControllerIT.java
            │   ├── UserControllerIT.java
            │   └── UserFollowControllerIT.java
            ├── AuthApiControllerIT.java
            ├── AuthorControllerIT.java
            ├── BookControllerIT.java
            ├── ChapterControllerIT.java
            ├── CharacterControllerIT.java
            ├── ReviewControllerIT.java
            └── SeriesControllerIT.java

docs/
├── database.md
├── project_structure.md
└── user_stories.md
