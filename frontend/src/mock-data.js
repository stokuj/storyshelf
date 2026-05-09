export const mockBookshelfEntries = [
  {
    id: 1,
    status: 'READING',
    book: {
      id: 1,
      title: 'The Fellowship of the Ring',
      author: 'J.R.R. Tolkien',
    },
  },
  {
    id: 2,
    status: 'WANT_TO_READ',
    book: {
      id: 2,
      title: 'A Game of Thrones',
      author: 'George R.R. Martin',
    },
  },
  {
    id: 3,
    status: 'READ',
    book: {
      id: 3,
      title: 'Dune',
      author: 'Frank Herbert',
    },
  },
]

export const mockProfile = {
  username: 'frodo',
  bio: 'Czytelnik fantasy, fan długich serii i map na końcu książki.',
  avatarUrl: '',
  memberSince: '2024-03-15T18:40:00',
}

export const mockSettings = {
  username: 'frodo',
  bio: 'Czytelnik fantasy, fan długich serii i map na końcu książki.',
  avatarUrl: '',
  memberSince: '2024-03-15T18:40:00',
  profilePublic: true,
  email: 'frodo@shire.pl',
  role: 'USER',
}
