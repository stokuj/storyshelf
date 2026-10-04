# Gotchas — środowisko dev i praca z agentem

> Nieoczywiste pułapki, na które już trafiliśmy. Każdy wpis: objaw → przyczyna → co robić.
> Dopisuj, gdy coś kosztowało więcej niż jedną próbę.

## Worktree i guard Claude Code

Sesja odizolowana w worktree (`.claude/worktrees/…`) ma guard, który odrzuca polecenia, o których nie umie udowodnić, że zostają w worktree.

| Odrzucane | Działa |
|---|---|
| `export OPENROUTER_API_KEY=...` | `uv run --env-file /home/dv6/GitHub/storyshelf/infra/.env ...` |
| `gh pr create --body "$(cat <<EOF ...)"` | treść do pliku tymczasowego, potem `--body-file` |
| `cat > plik <<'EOF' ... EOF` w łańcuchu z `&&` | zapis pliku narzędziem Write, potem osobne polecenie |
| `git -C ..` / `git -C <inny worktree>` | zwykłe polecenie uruchomione z katalogu worktree |
| `for f in ...; do ...; done` | osobne, proste polecenia |

Operacje git na innym worktree lub na głównym checkoucie (pull, sprzątanie): najpierw wyjdź z worktree (`ExitWorktree keep`).

## Frontend

- **Prettier tylko w `frontend/`.** `npx prettier --write` na pliku z `docs/` przeformatuje tabele Markdown (wyrównanie kolumn) i zaśmieci diff. Formatuj ścieżki pod `frontend/` albo `npm run format`.
- **TypeScript przypięty do `~6.0`.** typescript-eslint ma peer `typescript <6.1.0`, a TS 7 nie ma jeszcze API programowego. Pozostałe paczki instalujemy `@latest`. Upgrade, gdy typescript-eslint wspiera TS 7.1. Node 24 (`frontend/.nvmrc`).
- **`routeTree.gen.ts` jest commitowany.** CI po buildzie sprawdza `git diff --exit-code src/routeTree.gen.ts` — po dodaniu trasy zacommituj wygenerowany plik.

## Backend

- **Throttle rejestracji na żywym serwerze.** `runserver` egzekwuje `auth_register = 5/hour` (`config/settings/base.py`); w testach (`manage.py test`, pytest) throttle jest wyłączony. Seria rejestracji z ręki lub E2E → `429`. Podnieś przez env: `THROTTLE_AUTH_REGISTER`, `THROTTLE_AUTH_LOGIN`, `THROTTLE_AUTH_REFRESH`.
- **Django padło po auto-reloadzie.** Jeśli podczas reloadu `db` jest chwilowo nieosiągalna, `runserver` gubi wątek główny i przestaje słuchać na `:8000`, a kontener dalej jest „Up”. Sprawdź: `docker exec storyshelf-django sh -c "ss -ltn | grep 8000"`. Fix: `docker restart storyshelf-django`.
