<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { setMode } from 'mode-watcher';
	import { User, Settings, LogOut, Sun, Moon } from 'lucide-svelte';
	import { Avatar, AvatarFallback, AvatarImage } from '$lib/components/ui/avatar';
	import {
		DropdownMenu,
		DropdownMenuTrigger,
		DropdownMenuContent,
		DropdownMenuItem,
		DropdownMenuSeparator
	} from '$lib/components/ui/dropdown-menu';
	import { Button } from '$lib/components/ui/button';
	import type { UserMe } from '$lib/api/user';

	interface Props {
		user: UserMe | null | undefined;
	}
	let { user }: Props = $props();

	function initials(name: string): string {
		return name
			.split(' ')
			.slice(0, 2)
			.map((n) => n[0])
			.join('')
			.toUpperCase();
	}
</script>

{#if user}
	<DropdownMenu>
		<DropdownMenuTrigger>
			<Button variant="ghost" size="icon" class="rounded-full">
				<Avatar class="size-7">
					<AvatarImage src={user.avatar_url ?? undefined} alt={user.display_name} />
					<AvatarFallback>{initials(user.display_name)}</AvatarFallback>
				</Avatar>
			</Button>
		</DropdownMenuTrigger>
		<DropdownMenuContent align="end" class="w-48">
			<DropdownMenuItem onclick={() => goto(resolve(`/u/${user.handle}`))}>
				<User class="mr-2 size-4" /> Profile
			</DropdownMenuItem>
			<DropdownMenuItem onclick={() => goto(resolve('/settings'))}>
				<Settings class="mr-2 size-4" /> Settings
			</DropdownMenuItem>
			<DropdownMenuSeparator />
			<DropdownMenuItem onclick={() => setMode('dark')}>
				<Moon class="mr-2 size-4" /> Dark mode
			</DropdownMenuItem>
			<DropdownMenuItem onclick={() => setMode('light')}>
				<Sun class="mr-2 size-4" /> Light mode
			</DropdownMenuItem>
			<DropdownMenuSeparator />
			<form method="POST" action="/logout">
				<DropdownMenuItem>
					<button type="submit" class="flex w-full items-center">
						<LogOut class="mr-2 size-4" /> Sign out
					</button>
				</DropdownMenuItem>
			</form>
		</DropdownMenuContent>
	</DropdownMenu>
{:else}
	<Button variant="ghost" size="sm" href={resolve('/login')}>Sign in</Button>
{/if}
