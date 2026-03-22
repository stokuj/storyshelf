com.stokuj.books/
│
├── config/
│   ├── FlywayConfig.java
│   └── OpenApiConfig.java
│
├── controller/
│   ├── advice/
│   │   └── GlobalExceptionHandler.java
│   ├── api/
│   │   ├── admin/
│   │   │   └── AdminBookApiController.java
│   │   ├── AuthorController.java
│   │   ├── BookController.java
│   │   ├── CharacterApiController.java
│   │   ├── FollowController.java
│   │   ├── ReviewApiController.java
│   │   ├── SearchController.java
│   │   ├── SeriesController.java
│   │   ├── TagController.java
│   │   ├── UserBookController.java
│   │   └── UserProfileApiController.java
│   ├── integration/
│   │   └── FastApiCallbackController.java
│   └── web/
│       ├── AdminReviewWebController.java
│       ├── AdminWebController.java
│       ├── AuthorWebController.java
│       ├── AuthWebController.java
│       ├── BookshelfWebController.java
│       ├── BookWebController.java
│       ├── CurrentUserModelAdvice.java
│       ├── HomeController.java
│       ├── ReviewWebController.java
│       ├── SeriesWebController.java
│       ├── UserProfileWebController.java
│       └── UserSettingsController.java
│
├── domain/
│   ├── entity/
│   │   ├── Author.java
│   │   ├── Book.java
│   │   ├── BookCharacter.java
│   │   ├── BookChapter.java
│   │   ├── CharacterRelation.java
│   │   ├── Review.java
│   │   ├── Series.java
│   │   ├── StoryCharacter.java
│   │   ├── Tag.java
│   │   ├── User.java
│   │   ├── UserBook.java
│   │   └── UserFollow.java
│   └── enums/
│       ├── AuthorRole.java
│       ├── ReadingStatus.java
│       ├── Role.java
│       └── SeriesStatus.java
│
├── dto/
│   ├── author/
│   │   ├── AuthorRequest.java
│   │   └── AuthorResponse.java
│   ├── book/
│   │   ├── BookPatchRequest.java
│   │   ├── BookRequest.java
│   │   ├── BookResponse.java
│   │   └── BookSummaryResponse.java
│   ├── character/
│   │   ├── CharacterRelationResponse.java
│   │   └── CharacterResponse.java
│   ├── follow/
│   │   └── FollowResponse.java
│   ├── integration/
│   │   ├── AnalyseResponse.java
│   │   ├── AnalyseStats.java
│   │   ├── BookFindPairsResult.java
│   │   └── NerResult.java
│   ├── review/
│   │   ├── ReviewRequest.java
│   │   └── ReviewResponse.java
│   ├── series/
│   │   ├── SeriesRequest.java
│   │   └── SeriesResponse.java
│   ├── tag/
│   │   ├── TagRequest.java
│   │   └── TagResponse.java
│   └── user/
│       ├── LoginRequest.java
│       ├── RegisterRequest.java
│       ├── UserBookRequest.java
│       ├── UserBookResponse.java
│       ├── UserProfileResponse.java
│       ├── UserProfileUpdateRequest.java
│       ├── UserProfileVisibilityRequest.java
│       └── UserSettingsResponse.java
│
├── exception/
│   ├── ConflictException.java
│   ├── ResourceNotFoundException.java
│   └── UnauthorizedException.java
│
├── integration/
│   ├── kafka/
│   │   └── ChapterEventProducer.java
│   └── processor/
│       ├── NerResultProcessor.java
│       └── RelationsResultProcessor.java
│
├── repository/
│   ├── specification/
│   │   └── BookSpecification.java
│   ├── AuthorRepository.java
│   ├── BookCharacterRepository.java
│   ├── BookChapterRepository.java
│   ├── BookRepository.java
│   ├── CharacterRelationRepository.java
│   ├── ReviewRepository.java
│   ├── SeriesRepository.java
│   ├── StoryCharacterRepository.java
│   ├── TagRepository.java
│   ├── UserBookRepository.java
│   ├── UserFollowRepository.java
│   └── UserRepository.java
│
├── security/
│   ├── FastApiSecretFilter.java
│   ├── RoleConfig.java
│   ├── SecurityConfig.java
│   └── UserDetailsServiceImpl.java
│
├── service/
│   ├── AuthorService.java
│   ├── BookCharacterAggregator.java
│   ├── BookChapterService.java
│   ├── BookService.java
│   ├── ReviewService.java
│   ├── SeriesService.java
│   ├── StoryCharacterService.java
│   ├── TagService.java
│   ├── UserBookService.java
│   ├── UserFollowService.java
│   └── UserProfileService.java
│
└── SpringShelfApplication.java

src/main/resources/
├── db/migration/
│   └── V1__init_schema.sql
├── templates/
│   ├── layout/
│   │   └── base.html
│   ├── admin-book-form.html
│   ├── admin-reviews.html
│   ├── author.html
│   ├── book.html
│   ├── bookshelf.html
│   ├── error.html
│   ├── home.html
│   ├── login.html
│   ├── profile.html
│   ├── register.html
│   ├── series.html
│   └── settings.html
├── application-dev.yml
└── application.yml

src/test/java/
├── service/
│   ├── AuthorServiceTest.java
│   ├── BookServiceTest.java
│   ├── ReviewServiceTest.java
│   ├── SeriesServiceTest.java
│   ├── StoryCharacterServiceTest.java
│   └── UserBookServiceTest.java
└── SpringShelfApplicationTests.java