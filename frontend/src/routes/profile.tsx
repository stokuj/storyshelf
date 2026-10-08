import { createFileRoute } from '@tanstack/react-router'
import { useProfile, useSetProfilePublic } from '@/api/hooks'
import type { Profile } from '@/api/types'

export const Route = createFileRoute('/profile')({
  component: ProfilePage,
})

function ProfilePage() {
  const { data: profile } = useProfile()
  const setPublic = useSetProfilePublic()
  if (!profile) return null
  // Ulubione are book or character Pages; the Path prefix tells which
  const favorites = (prefix: string) => profile.favorites.filter((f) => f.path.startsWith(prefix))

  return (
    <section className="max-w-2xl">
      <header className="flex items-center gap-4">
        <span
          aria-hidden
          className="grid size-14 place-items-center rounded-full bg-primary text-lg font-semibold text-primary-foreground"
        >
          {profile.handle.slice(0, 2).toUpperCase()}
        </span>
        <h1 className="font-heading text-3xl">@{profile.handle}</h1>
        <label className="ml-auto flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            role="switch"
            checked={profile.is_public}
            onChange={(e) => setPublic.mutate(e.target.checked)}
          />
          Public profile
        </label>
      </header>

      <h2 className="mt-8 font-heading text-xl">About me</h2>
      <p className="mt-2">{profile.about}</p>

      <Favorites title="Favourite books" items={favorites('/books/')} />
      <Favorites title="Favourite characters" items={favorites('/characters/')} />

      <p className="mt-10 text-sm text-muted-foreground">
        Visitors see these as cards only. Your wiki pages stay private.
      </p>
    </section>
  )
}

// Cards only (title + description), no link: CONTEXT — visitors never reach the Page
function Favorites({ title, items }: { title: string; items: Profile['favorites'] }) {
  if (items.length === 0) return null
  return (
    <section className="mt-8">
      <h2 className="font-heading text-xl">{title}</h2>
      <ul className="mt-3 grid grid-cols-2 gap-3">
        {items.map((f) => (
          <li key={f.path} className="rounded-md border p-4">
            <p className="font-semibold">{f.title}</p>
            <p className="mt-1 text-sm text-muted-foreground">{f.description}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
