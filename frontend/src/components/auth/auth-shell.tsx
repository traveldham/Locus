import { BrandLogo } from "@/components/common/brand-logo";
import { Buildings11, MapMarker5, Shield1Check } from "@tailgrids/icons";
import Image from "next/image";

const PILLARS = [
  {
    icon: Buildings11,
    title: "One workspace per organization",
    description: "Every teammate signs into a shared, secured workspace scoped to your organization.",
  },
  {
    icon: MapMarker5,
    title: "Every profile, one place",
    description: "See the profiles your organization operates from a single dashboard.",
  },
  {
    icon: Shield1Check,
    title: "Evidence before action",
    description: "Built so every future recommendation traces back to the data behind it.",
  },
];

export function AuthShell({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <main className="grid min-h-full bg-card-surface-area lg:grid-cols-[minmax(0,1fr)_minmax(28rem,0.8fr)]">
      <section className="flex items-center justify-center px-6 py-10 sm:px-10">
        <div className="w-full max-w-md">
          <BrandLogo />
          <h1 className="mt-14 text-3xl font-semibold tracking-[-0.03em] text-text-primary">{title}</h1>
          <p className="mt-3 max-w-sm text-sm leading-6 text-text-tertiary">{description}</p>
          {children}
        </div>
      </section>
      <aside className="hidden flex-col justify-between bg-[#44131B] p-12 lg:flex">
        <Image src="/brand/locus-logo.svg" alt="Locus Intelligence" width={300} height={106} className="h-14 w-auto brightness-0 invert" />
        <div className="max-w-lg">
          <span className="inline-flex items-center rounded-full bg-white/10 px-3 py-1 text-xs font-medium tracking-wide text-white/70 uppercase">Workspace</span>
          <p className="mt-6 text-4xl leading-tight font-semibold tracking-[-0.035em] text-white">Turn profile data into the next clear business decision.</p>
          <p className="mt-5 max-w-md text-base leading-7 text-white/60">A multi-profile decision-support workspace for operators and managers who need to know which profiles need attention, and why.</p>
          <ul className="mt-10 space-y-5">
            {PILLARS.map(({ icon: Icon, title, description }) => (
              <li key={title} className="flex items-start gap-4">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-white/10 text-white">
                  <Icon aria-hidden="true" focusable="false" className="size-4.5" />
                </span>
                <div>
                  <p className="text-sm font-medium text-white">{title}</p>
                  <p className="mt-1 text-sm leading-6 text-white/55">{description}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </main>
  );
}
