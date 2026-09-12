import { BrandLogo } from "@/components/common/brand-logo";

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
      <aside className="hidden items-end bg-background-gray-primary p-12 lg:flex">
        <div className="max-w-lg">
          <p className="text-4xl leading-tight font-semibold tracking-[-0.035em] text-text-primary">Turn location data into the next clear business decision.</p>
          <p className="mt-5 max-w-md text-base leading-7 text-text-tertiary">One secure workspace for your organization, locations, evidence, and recommendations.</p>
        </div>
      </aside>
    </main>
  );
}
