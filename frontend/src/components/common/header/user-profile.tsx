"use client";

import { LogoutIcon } from "@/components/common/header/icons";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/tailgrids/core/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuHeader,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/tailgrids/core/dropdown";
import { AltArrowDownIcon } from "@/utils/icon";
import { useAuth } from "@/contexts/auth-context";

interface UserProfile {
  name: string;
  email: string;
  avatarUrl?: string;
}

export function UserProfileButton() {
  const { user: account, logout } = useAuth();
  const user: UserProfile = {
    name: account?.full_name ?? account?.email ?? "Account",
    email: account?.email ?? "",
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="group flex items-center gap-2.5 rounded-lg border-0 p-0 transition-all outline-none focus-visible:ring-4 focus-visible:ring-input-primary-focus-border/20 focus-visible:ring-offset-1">
        <Avatar>
          <AvatarImage src={user.avatarUrl!} alt={user.name} className="size-10 rounded-lg" />
          <AvatarFallback className="rounded-lg border border-border-secondary-alt bg-background-gray-secondary_alt">
            {user.name.charAt(0)}
          </AvatarFallback>
        </Avatar>

        <span className="text-sm leading-5 font-medium text-text-primary">{user.name}</span>

        <AltArrowDownIcon className="text-icon-tertiary transition-transform duration-200 group-aria-expanded:-rotate-180" />
      </DropdownMenuTrigger>

      <DropdownMenuContent placement="bottom end" className="w-70 overflow-hidden p-0 shadow-3xl">
        <DropdownMenuHeader className="flex w-full items-center justify-start gap-2 border-b border-border-secondary-alt px-4 py-3">
          <Avatar size="md">
            <AvatarImage src={user.avatarUrl!} alt={user.name} />
            <AvatarFallback className="border border-border-secondary-alt bg-background-gray-secondary_alt">
              {user.name.charAt(0)}
            </AvatarFallback>
          </Avatar>
          <span className="flex flex-col">
            <span className="text-sm font-medium text-text-primary">{user.name}</span>
            <span className="truncate text-xs text-gray-500">{user.email}</span>
          </span>
        </DropdownMenuHeader>

        <DropdownMenuItem
          onAction={() => void logout()}
          className="m-1.5 w-auto cursor-pointer px-3 py-2.5"
        >
          <span className="text-icon-secondary group-hover:text-text-primary">
            <LogoutIcon />
          </span>
          <span className="leading-5">Logout</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
