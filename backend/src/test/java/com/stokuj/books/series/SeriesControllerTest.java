package com.stokuj.books.series;

import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.series.dto.SeriesRequest;
import com.stokuj.books.series.dto.SeriesResponse;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;

@ExtendWith(MockitoExtension.class)
class SeriesControllerTest {

    private static ValidatorFactory validatorFactory;
    private static Validator validator;

    @Mock
    SeriesRepository seriesRepository;

    @InjectMocks
    SeriesController seriesController;

    @BeforeAll
    static void setUpValidator() {
        validatorFactory = Validation.buildDefaultValidatorFactory();
        validator = validatorFactory.getValidator();
    }

    @AfterAll
    static void closeValidator() {
        validatorFactory.close();
    }

    @Nested
    class GetAll {

        @Test
        void shouldReturnAllSeries() {
            Series s1 = series(1L, "The Wheel of Time", "Epic fantasy series", SeriesStatus.COMPLETED);
            Series s2 = series(2L, "The Stormlight Archive", "Cosmere epic", SeriesStatus.ONGOING);
            given(seriesRepository.findAll()).willReturn(List.of(s1, s2));

            ResponseEntity<List<SeriesResponse>> response = seriesController.getAll();

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).hasSize(2);
            assertThat(response.getBody().get(0).name()).isEqualTo("The Wheel of Time");
            assertThat(response.getBody().get(1).name()).isEqualTo("The Stormlight Archive");
        }

        @Test
        void shouldReturnEmptyListWhenNoSeries() {
            given(seriesRepository.findAll()).willReturn(List.of());

            ResponseEntity<List<SeriesResponse>> response = seriesController.getAll();

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isEmpty();
        }
    }

    @Nested
    class GetById {

        @Test
        void shouldReturnSeriesById() {
            Series s = series(10L, "The Expanse Saga", "Space opera", SeriesStatus.COMPLETED);
            given(seriesRepository.findById(10L)).willReturn(Optional.of(s));

            ResponseEntity<SeriesResponse> response = seriesController.getById(10L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().id()).isEqualTo(10L);
            assertThat(response.getBody().name()).isEqualTo("The Expanse Saga");
        }

        @Test
        void shouldThrowWhenSeriesNotFound() {
            given(seriesRepository.findById(404L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> seriesController.getById(404L))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Series not found");
        }
    }

    @Nested
    class Create {

        @Test
        void shouldCreateSeries() {
            SeriesRequest request = new SeriesRequest("The First Law", "Dark fantasy trilogy", SeriesStatus.COMPLETED);
            Series saved = series(3L, "The First Law", "Dark fantasy trilogy", SeriesStatus.COMPLETED);
            given(seriesRepository.save(org.mockito.ArgumentMatchers.any(Series.class))).willReturn(saved);

            ResponseEntity<SeriesResponse> response = seriesController.create(request);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().id()).isEqualTo(3L);
            assertThat(response.getBody().name()).isEqualTo("The First Law");
        }

        @Test
        void shouldHaveValidationViolationsForInvalidPayload() {
            SeriesRequest invalid = new SeriesRequest("short", "desc", null);

            Set<ConstraintViolation<SeriesRequest>> violations = validator.validate(invalid);

            assertThat(violations).isNotEmpty();
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("name"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("status"));
        }
    }

    @Nested
    class Update {

        @Test
        void shouldUpdateExistingSeries() {
            Series existing = series(5L, "Old Name Series", "Old description", SeriesStatus.ONGOING);
            SeriesRequest request = new SeriesRequest("Updated Name", "Updated description", SeriesStatus.COMPLETED);
            Series saved = series(5L, "Updated Name", "Updated description", SeriesStatus.COMPLETED);

            given(seriesRepository.findById(5L)).willReturn(Optional.of(existing));
            given(seriesRepository.save(existing)).willReturn(saved);

            ResponseEntity<SeriesResponse> response = seriesController.update(5L, request);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().name()).isEqualTo("Updated Name");
            assertThat(response.getBody().status()).isEqualTo(SeriesStatus.COMPLETED);
        }

        @Test
        void shouldThrowWhenUpdatingMissingSeries() {
            SeriesRequest request = new SeriesRequest("Updated Name", "Updated description", SeriesStatus.COMPLETED);
            given(seriesRepository.findById(999L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> seriesController.update(999L, request))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Series not found");
        }
    }

    @Nested
    class Delete {

        @Test
        void shouldDeleteSeriesAndReturnNoContent() {
            ResponseEntity<Void> response = seriesController.delete(12L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
        }
    }

    private Series series(Long id, String name, String description, SeriesStatus status) {
        Series series = new Series();
        setField(series, "id", id);
        setField(series, "name", name);
        setField(series, "description", description);
        setField(series, "status", status);
        return series;
    }

    private void setField(Object target, String fieldName, Object value) {
        try {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            field.set(target, value);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }
}
