from django.test import SimpleTestCase

from wiki import okf

BOOK = (
    "---\ntype: book\ntitle: Solaris\n---\n\n"
    "## Streszczenie\n\n## Postacie\n\n## Miejsca\n\n## Wątki i motywy\n"
)


class ValidateTest(SimpleTestCase):
    def assert_error(self, content, page_type, message, field="content"):
        with self.assertRaises(okf.OKFError) as ctx:
            okf.validate(content, page_type)
        self.assertEqual(str(ctx.exception), message)
        self.assertEqual(ctx.exception.field, field)

    def test_deeply_nested_frontmatter_is_rejected(self):
        content = "---\nx: " + "[" * 20000 + "]" * 20000 + "\n---\n\n# Body\n"
        self.assert_error(content, "book", "Invalid frontmatter: too deeply nested")

    def test_valid_book_returns_frontmatter(self):
        self.assertEqual(okf.validate(BOOK, "book"), {"type": "book", "title": "Solaris"})

    def test_crlf_line_endings_are_valid(self):
        okf.validate(BOOK.replace("\n", "\r\n"), "book")

    def test_extra_sections_are_allowed(self):
        okf.validate(BOOK + "\n## Ciekawostki\n\nTekst.\n", "book")

    def test_missing_frontmatter(self):
        self.assert_error("## Streszczenie\n", "book", "Invalid frontmatter: Missing frontmatter")

    def test_broken_yaml(self):
        with self.assertRaises(okf.OKFError) as ctx:
            okf.validate("---\ntype: [book\n---\n", "book")
        self.assertTrue(str(ctx.exception).startswith("Invalid frontmatter: "))

    def test_frontmatter_not_a_mapping(self):
        self.assert_error("---\n- a\n---\n", "book", "Invalid frontmatter: not a mapping")

    def test_missing_type(self):
        self.assert_error(BOOK.replace("type: book\n", ""), "book", "Missing type")

    def test_type_must_match_page(self):
        self.assert_error(BOOK, "character", "Page type can't change")

    def test_missing_title(self):
        self.assert_error(BOOK.replace("title: Solaris\n", ""), "book", "Missing title")

    def test_blank_title(self):
        self.assert_error(BOOK.replace("title: Solaris", "title: ' '"), "book", "Missing title")

    def test_fields_the_ui_cannot_render_are_rejected(self):
        cases = {
            "description: 2024": 'description must be text (quote numbers, e.g. "1984")',
            "verified: x": "verified must be a list of objects",
            "sources:\n  - id: 1\n    resource: 2": "sources must be a list of objects",
            "generated: agent": "generated must be an object",
        }
        for yaml_line, message in cases.items():
            with self.subTest(yaml_line):
                content = BOOK.replace("title: Solaris\n", f"title: Solaris\n{yaml_line}\n")
                self.assert_error(content, "book", f"Invalid frontmatter: {message}")

    def test_empty_optional_values_are_valid(self):
        okf.validate(BOOK.replace("title: Solaris\n", "title: Solaris\ndescription:\n"), "book")

    def test_missing_template_headings_are_listed_in_template_order(self):
        content = BOOK.replace("## Postacie\n", "").replace("## Miejsca\n", "")
        self.assert_error(content, "book", "Missing template headings: Postacie, Miejsca")


class PathTest(SimpleTestCase):
    def test_slugify(self):
        self.assertEqual(okf.slugify("Krew elfów"), "krew-elfow")
        self.assertEqual(okf.slugify("Łódź"), "lodz")
        self.assertEqual(okf.slugify("Diuna: Mesjasz"), "diuna-mesjasz")
        self.assertEqual(okf.slugify(" -Ostatnie życzenie!- "), "ostatnie-zyczenie")

    def test_page_path_per_type(self):
        self.assertEqual(okf.page_path("book", "Krew elfów"), "/books/krew-elfow.md")
        self.assertEqual(okf.page_path("universe", "Wiedźmin"), "/universes/wiedzmin.md")
        self.assertEqual(
            okf.page_path("character", "Geralt", "/books/krew-elfow.md"),
            "/characters/geralt--krew-elfow.md",
        )
        self.assertEqual(
            okf.page_path("place", "Kaer Morhen", "/books/krew-elfow.md"),
            "/places/kaer-morhen--krew-elfow.md",
        )

    def test_title_without_letters_or_digits_is_rejected(self):
        with self.assertRaises(okf.OKFError) as ctx:
            okf.page_path("book", "!!!")
        self.assertEqual(ctx.exception.field, "title")


class RenderTemplateTest(SimpleTestCase):
    def test_every_template_passes_validation(self):
        for page_type in okf.TEMPLATES:
            with self.subTest(page_type=page_type):
                content = okf.render_template(page_type, {"title": "X"})
                okf.validate(content, page_type)

    def test_book_template_frontmatter(self):
        content = okf.render_template(
            "book", {"title": "Diuna: Mesjasz", "author": "Frank Herbert", "year": 1969,
                     "universe": None},
        )
        frontmatter, body = okf.parse(content)
        self.assertEqual(frontmatter, {
            "type": "book", "title": "Diuna: Mesjasz", "author": "Frank Herbert", "year": 1969,
            "status": "draft",
        })
        self.assertTrue(body.startswith("## Streszczenie\n"))
