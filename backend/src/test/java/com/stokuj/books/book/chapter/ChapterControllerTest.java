package com.stokuj.books.book.chapter;

import com.stokuj.books.book.chapter.dto.ChapterResponse;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.mock.web.MockMultipartFile;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class ChapterControllerTest {

    @Mock
    BookChapterService bookChapterService;

    @InjectMocks
    ChapterController chapterController;

    @Nested
    class GetChapters {

        @Test
        void shouldReturnChaptersForBook() {
            List<ChapterResponse> chapters = List.of(
                    new ChapterResponse(1L, 10L, 1, "Chapter 1", false, 1000, 900, 200, 300),
                    new ChapterResponse(2L, 10L, 2, "Chapter 2", true, 1100, 980, 220, 320)
            );
            given(bookChapterService.getChapters(10L)).willReturn(chapters);

            ResponseEntity<List<ChapterResponse>> response = chapterController.getChapters(10L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).hasSize(2);
            assertThat(response.getBody().get(0).chapterNumber()).isEqualTo(1);
            assertThat(response.getBody().get(1).chapterNumber()).isEqualTo(2);
        }
    }

    @Nested
    class UploadContent {

        @Test
        void shouldUploadContentAndReturnCreated() throws Exception {
            MockMultipartFile file = new MockMultipartFile(
                    "file",
                    "chapters.txt",
                    "text/plain",
                    " Chapter 1\ncontent ".getBytes(StandardCharsets.UTF_8)
            );
            given(bookChapterService.loadContent(10L, "Chapter 1\ncontent")).willReturn(7);

            ResponseEntity<Map<String, Object>> response = chapterController.uploadContent(10L, file);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().get("bookId")).isEqualTo(10L);
            assertThat(response.getBody().get("chaptersCreated")).isEqualTo(7);
        }
    }

    @Nested
    class ClearContent {

        @Test
        void shouldClearContentAndReturnNoContent() {
            ResponseEntity<Void> response = chapterController.clearContent(10L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
            verify(bookChapterService).clearContent(10L);
        }
    }
}
