com.stokuj.books/
├── SpringShelfApplication.java
├── config/
│   ├── FlywayConfig.java
│   └── OpenApiConfig.java
├── controller/
│   ├── advice/
│   │   └── GlobalExceptionHandler.java
│   ├── api/
│   │   ├── admin/
│   │   │   ├── AdminAuthorController.java
│   │   │   ├── AdminBookController.java
│   │   │   ├── AdminChapterController.java
│   │   │   ├── AdminReviewController.java
│   │   │   └── AdminSeriesController.java
│   │   ├── user/
│   │   │   ├── BookShelfController.java
│   │   │   ├── UserController.java
│   │   │   └── UserFollowController.java
│   │   ├── AuthApiController.java
│   │   ├── AuthorController.java
│   │   ├── BookController.java
│   │   ├── ChapterController.java
│   │   ├── CharacterController.java
│   │   ├── ReviewController.java
│   │   └── SeriesController.java
│   ├── integration/
│   │   └── FastApiCallbackController.java
│   └── web/
│       ├── AdminReviewWebController.java
│       ├── AdminWebController.java
│       ├── AuthWebController.java
│       ├── CurrentUserModelAdvice.java
│       ├── HomeController.java
│       ├── ReviewWebController.java
│       ├── UserBookWebController.java
│       ├── UserProfileWebController.java
│       └── UserSettingsController.java
├── domain/
│   ├── entity/
│   │   ├── Author.java
│   │   ├── BookAuthor.java
│   │   ├── BookCharacter.java
│   │   ├── Book.java
│   │   ├── BookTag.java
│   │   ├── Chapter.java
│   │   ├── Character.java
│   │   ├── CharacterRelation.java
│   │   ├── Review.java
│   │   ├── Series.java
│   │   ├── Tag.java
│   │   ├── UserBook.java
│   │   ├── UserFollow.java
│   │   └── User.java
│   └── enums/
│       ├── AuthorRole.java
│       ├── ReadingStatus.java
│       ├── Role.java
│       └── SeriesStatus.java
├── dto/
│   ├── auth/
│   │   ├── AuthResponse.java
│   │   ├── LoginRequest.java
│   │   └── RegisterRequest.java
│   ├── author/
│   │   ├── AuthorRequest.java
│   │   └── AuthorResponse.java
│   ├── book/
│   │   ├── AdminBookForm.java
│   │   ├── BookPatchRequest.java
│   │   ├── BookRequest.java
│   │   └── BookResponse.java
│   ├── bookshelf/
│   │   ├── UserBookRequest.java
│   │   └── UserBookResponse.java
│   ├── chapter/
│   │   └── ChapterResponse.java
│   ├── character/
│   │   ├── CharacterRelationResponse.java
│   │   └── CharacterResponse.java
│   ├── follow/
│   │   └── FollowResponse.java
│   ├── integration/
│   │   ├── AnalyseResponse.java
│   │   ├── AnalyseStats.java
│   │   ├── BookFindPairsResult.java
│   │   ├── NerResult.java
│   │   └── PairResult.java
│   ├── review/
│   │   ├── ReviewRequest.java
│   │   └── ReviewResponse.java
│   ├── series/
│   │   ├── SeriesRequest.java
│   │   └── SeriesResponse.java
│   └── user/
│       ├── UserProfileResponse.java
│       ├── UserProfileUpdateRequest.java
│       └── UserSettingsResponse.java
├── exception/
│   ├── ConflictException.java
│   ├── ResourceNotFoundException.java
│   └── UnauthorizedException.java
├── integration/
│   ├── kafka/
│   │   └── ChapterEventProducer.java
│   └── processor/
│       ├── NerResultProcessor.java
│       └── RelationsResultProcessor.java
├── repository/
│   ├── AuthorRepository.java
│   ├── BookAuthorRepository.java
│   ├── BookChapterRepository.java
│   ├── BookCharacterRepository.java
│   ├── BookRepository.java
│   ├── BookTagRepository.java
│   ├── CharacterRelationRepository.java
│   ├── CharacterRepository.java
│   ├── ReviewRepository.java
│   ├── SeriesRepository.java
│   ├── TagRepository.java
│   ├── UserBookRepository.java
│   ├── UserFollowRepository.java
│   └── UserRepository.java
├── security/
│   ├── FastApiSecretFilter.java
│   ├── RoleConfig.java
│   ├── SecurityConfig.java
│   └── UserDetailsServiceImpl.java
└── service/
    ├── AuthService.java
    ├── BookChapterService.java
    ├── BookCharacterAggregator.java
    ├── BookService.java
    ├── CharacterService.java
    ├── ReviewService.java
    ├── UserBookService.java
    └── UserProfileService.java

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
    ├── config/
    │   └── TestSecurityConfig.java
    ├── controller/
    │   ├── api/
    │   │   ├── admin/
    │   │   │   ├── AdminAuthorControllerIT.java
    │   │   │   ├── AdminBookControllerIT.java
    │   │   │   ├── AdminChapterControllerIT.java
    │   │   │   ├── AdminReviewControllerIT.java
    │   │   │   └── AdminSeriesControllerIT.java
    │   │   ├── user/
    │   │   │   ├── BookShelfControllerIT.java
    │   │   │   ├── UserControllerIT.java
    │   │   │   └── UserFollowControllerIT.java
    │   │   ├── AuthApiControllerIT.java
    │   │   ├── AuthorControllerIT.java
    │   │   ├── BookControllerIT.java
    │   │   ├── ChapterControllerIT.java
    │   │   ├── CharacterControllerIT.java
    │   │   ├── ReviewControllerIT.java
    │   │   └── SeriesControllerIT.java
    │   └── integration/
    │       └── FastApiCallbackControllerIT.java
    └── dto/
        └── service/
            └── BookServiceTest.java
