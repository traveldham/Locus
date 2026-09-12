import { buttonStyles } from "@/components/tailgrids/core/button";
import { cn } from "@/utils/cn";
import Link from "next/link";
import type { ReactNode } from "react";

interface LinkButtonProps {
  href: string;
  children: ReactNode;
  variant?: "primary" | "danger" | "success";
  appearance?: "fill" | "outline" | "ghost";
  size?: "sm" | "md" | "lg" | "xl" | "xxl";
  /** Opens in a new tab — used for the actions that only Google's own dashboard can complete. */
  external?: boolean;
  className?: string;
}

export function LinkButton({
  href,
  children,
  variant = "primary",
  appearance = "fill",
  size = "xl",
  external = false,
  className,
}: LinkButtonProps) {
  const classes = cn(
    buttonStyles({ variant, appearance, size, iconOnly: false }),
    "no-underline focus-visible:ring-4",
    className,
  );

  if (external) {
    return (
      <a href={href} target="_blank" rel="noreferrer noopener" className={classes}>
        {children}
      </a>
    );
  }

  return (
    <Link href={href} className={classes}>
      {children}
    </Link>
  );
}
