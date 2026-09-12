import { ArrowLeft } from "@tailgrids/icons";
import Link from "next/link";
import type { ReactNode } from "react";

interface BackLinkProps {
  href: string;
  children: ReactNode;
}

export function BackLink({ href, children }: BackLinkProps) {
  return (
    <Link
      href={href}
      className="-mt-2 -ml-2.5 mb-1 inline-flex h-11 items-center gap-1.5 rounded-lg px-2.5 text-sm font-medium text-text-tertiary transition hover:bg-background-gray-secondary hover:text-text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
    >
      <ArrowLeft aria-hidden="true" focusable="false" className="size-4" />
      {children}
    </Link>
  );
}
