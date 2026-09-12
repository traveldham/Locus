import { cn } from "@/utils/cn";
import Image from "next/image";
import Link from "next/link";

// The brand assets are dark-on-transparent, so anything sitting on a dark surface has to
// be inverted to stay visible. `onDark` is for surfaces that are dark in BOTH themes —
// the sidebar — where the `dark:` variant would leave the mark invisible in light mode.
const invertOnDark = "brightness-0 invert";

export function BrandMark({ onDark = false }: { onDark?: boolean }) {
  return (
    <span className="flex size-11 shrink-0 items-center justify-center" aria-hidden="true">
      <Image
        src="/brand/favicon.webp"
        alt=""
        width={180}
        height={180}
        className={cn("size-9 object-contain", onDark ? invertOnDark : "dark:brightness-0 dark:invert")}
      />
    </span>
  );
}

export function BrandLogo({ compact = false, onDark = false }: { compact?: boolean; onDark?: boolean }) {
  return (
    <Link
      href="/"
      aria-label="Locus Intelligence dashboard"
      className="flex min-h-11 items-center rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-600"
    >
      {compact ? (
        <BrandMark onDark={onDark} />
      ) : (
        <Image
          src="/brand/locus-logo.svg"
          alt="Locus Intelligence"
          width={300}
          height={106}
          priority
          className={cn("h-9 w-auto", onDark ? invertOnDark : "dark:brightness-0 dark:invert")}
        />
      )}
    </Link>
  );
}
