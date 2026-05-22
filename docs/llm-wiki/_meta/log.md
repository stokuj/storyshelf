# Log operacji wiki

Append-only dziennik komend `/wiki-lint` i `/wiki-ingest`. Każdy wpis jednej linii:
`## [YYYY-MM-DD HH:MM] <komenda> | <wynik 1-linijka>`.

Nigdy nie nadpisuj wcześniejszych wpisów — tylko dopisuj nowe.

## [2026-05-22] init | utworzono 5 stron seed (auth-flow, nlp-pipeline, api-conventions, celery-workers, dev-setup) + INDEX
## [2026-05-22] wiki-lint | 0 errors, 4 warnings — brakujące back-refs (R2): api-conventions↔nlp-pipeline, auth-flow→dev-setup, dev-setup→api-conventions, nlp-pipeline→dev-setup
## [2026-05-22] wiki-lint --fix | dodano back-refs: nlp-pipeline+api-conventions, dev-setup+auth-flow, dev-setup+nlp-pipeline, api-conventions+dev-setup → graf domknięty, 0 warnings
