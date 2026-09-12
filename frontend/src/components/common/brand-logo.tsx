import Image from "next/image";
import Link from "next/link";

export function BrandMark() {
  return (
    <span className="flex size-11 shrink-0 items-center justify-center" aria-hidden="true">
      <Image src="/brand/favicon.webp" alt="" width={180} height={180} className="size-9 object-contain brightness-0 invert" />
    </span>
  );
}

export function BrandLogo({ compact = false }: { compact?: boolean }) {
  return (
    <Link href="/" aria-label="Locus Intelligence dashboard" className="flex min-h-11 items-center rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-600">
      {compact ? <BrandMark /> : <Image src="/brand/locus-logo.svg" alt="Locus Intelligence" width={300} height={106} priority className="h-9 w-auto dark:brightness-0 dark:invert" />}
    </Link>
  );
}
