package com.stokuj.books.controller;

import com.stokuj.books.dto.request.AdminBookForm;
import com.stokuj.books.dto.request.BookRequest;
import com.stokuj.books.service.BookService;
import com.stokuj.books.service.BookChapterService;
import jakarta.validation.Valid;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Controller
@RequestMapping("/admin")
public class AdminPageController {

    private final BookService bookService;
    private final BookChapterService bookChapterService;

    public AdminPageController(BookService bookService, BookChapterService bookChapterService) {
        this.bookService = bookService;
        this.bookChapterService = bookChapterService;
    }

    @PostMapping("/book/{id}/content")
    public String uploadBookContent(@PathVariable Long id,
                                    @RequestParam("file") MultipartFile file,
                                    RedirectAttributes redirectAttributes) {
        if (file == null || file.isEmpty()) {
            redirectAttributes.addFlashAttribute("contentMsg", "Wybierz plik .txt przed wysłaniem.");
            redirectAttributes.addFlashAttribute("contentMsgType", "error");
            return "redirect:/book/" + id;
        }

        String content;
        try {
            content = new String(file.getBytes(), StandardCharsets.UTF_8).strip();
        } catch (IOException e) {
            redirectAttributes.addFlashAttribute("contentMsg", "Nie udało się odczytać pliku.");
            redirectAttributes.addFlashAttribute("contentMsgType", "error");
            return "redirect:/book/" + id;
        }

        if (content.isBlank()) {
            redirectAttributes.addFlashAttribute("contentMsg", "Plik jest pusty.");
            redirectAttributes.addFlashAttribute("contentMsgType", "error");
            return "redirect:/book/" + id;
        }

        int chaptersCount = bookChapterService.loadContent(id, content);
        redirectAttributes.addFlashAttribute("contentMsg", "Treść wgrana. Rozdziałów: " + chaptersCount + ".");
        redirectAttributes.addFlashAttribute("contentMsgType", "success");
        return "redirect:/book/" + id;
    }

    @GetMapping("/books/new")
    public String newBookForm(Model model) {
        model.addAttribute("bookForm", new AdminBookForm());
        model.addAttribute("formTitle", "Dodaj książkę");
        model.addAttribute("formAction", "/admin/books/new");
        return "admin-book-form";
    }

    @PostMapping("/books/new")
    public String createBook(@Valid @ModelAttribute("bookForm") AdminBookForm form,
                             BindingResult bindingResult,
                             RedirectAttributes redirectAttributes,
                             Model model) {
        if (bindingResult.hasErrors()) {
            model.addAttribute("formTitle", "Dodaj książkę");
            model.addAttribute("formAction", "/admin/books/new");
            return "admin-book-form";
        }

        bookService.create(toBookRequest(form));
        redirectAttributes.addFlashAttribute("shelfMsg", "Dodano książkę do katalogu.");
        return "redirect:/";
    }

    @GetMapping("/books/{id}/edit")
    public String editBookForm(@PathVariable Long id, Model model) {
        model.addAttribute("bookForm", toForm(bookService.getById(id)));
        model.addAttribute("formTitle", "Edytuj książkę");
        model.addAttribute("formAction", "/admin/books/" + id + "/edit");
        model.addAttribute("bookId", id);
        return "admin-book-form";
    }

    @PostMapping("/books/{id}/edit")
    public String updateBook(@PathVariable Long id,
                             @Valid @ModelAttribute("bookForm") AdminBookForm form,
                             BindingResult bindingResult,
                             RedirectAttributes redirectAttributes,
                             Model model) {
        if (bindingResult.hasErrors()) {
            model.addAttribute("formTitle", "Edytuj książkę");
            model.addAttribute("formAction", "/admin/books/" + id + "/edit");
            model.addAttribute("bookId", id);
            return "admin-book-form";
        }

        bookService.update(id, toBookRequest(form));
        redirectAttributes.addFlashAttribute("shelfMsg", "Zaktualizowano książkę.");
        return "redirect:/book/" + id;
    }

    @PostMapping("/books/{id}/delete")
    public String deleteBook(@PathVariable Long id, RedirectAttributes redirectAttributes) {
        bookService.delete(id);
        redirectAttributes.addFlashAttribute("shelfMsg", "Usunięto książkę.");
        return "redirect:/";
    }

    private BookRequest toBookRequest(AdminBookForm form) {
        BookRequest request = new BookRequest();
        request.setTitle(form.getTitle());
        request.setAuthor(form.getAuthor());
        request.setYear(form.getYear() != null ? form.getYear() : 0);
        request.setIsbn(form.getIsbn());
        request.setDescription(form.getDescription());
        request.setPageCount(form.getPageCount() != null ? form.getPageCount() : 0);
        request.setGenres(parseSet(form.getGenres()));
        request.setTags(parseList(form.getTags()));
        return request;
    }

    private AdminBookForm toForm(com.stokuj.books.model.entity.Book book) {
        AdminBookForm form = new AdminBookForm();
        form.setTitle(book.getTitle());
        form.setAuthor(book.getAuthor());
        form.setYear(book.getYear());
        form.setIsbn(book.getIsbn());
        form.setDescription(book.getDescription());
        form.setPageCount(book.getPageCount());
        form.setGenres(joinCsv(book.getGenres()));
        form.setTags(joinCsv(book.getTags()));
        return form;
    }

    private Set<String> parseSet(String raw) {
        if (raw == null || raw.isBlank()) {
            return Set.of();
        }
        return Arrays.stream(raw.split(","))
                .map(String::trim)
                .filter(value -> !value.isBlank())
                .collect(Collectors.toCollection(LinkedHashSet::new));
    }

    private List<String> parseList(String raw) {
        if (raw == null || raw.isBlank()) {
            return List.of();
        }
        return Arrays.stream(raw.split(","))
                .map(String::trim)
                .filter(value -> !value.isBlank())
                .toList();
    }

    private String joinCsv(Set<String> values) {
        if (values == null || values.isEmpty()) {
            return "";
        }
        return String.join(", ", values);
    }

    private String joinCsv(List<String> values) {
        if (values == null || values.isEmpty()) {
            return "";
        }
        return String.join(", ", values);
    }
}
