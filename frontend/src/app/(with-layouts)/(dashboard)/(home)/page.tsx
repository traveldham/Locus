"use client";

import { useAuth } from "@/contexts/auth-context";

export default function Home() {
  const { user, activeOrganization } = useAuth();
  const firstName = (user?.full_name ?? "there").split(" ")[0];
  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <div className="max-w-3xl">
        <h1 className="text-[28px] leading-9 font-semibold tracking-[-0.03em] text-text-primary">Welcome, {firstName}</h1>
        <p className="mt-2 text-sm leading-6 text-text-tertiary">Your Locus Intelligence workspace is ready. Location data and decision tools will appear here as they are connected.</p>
      </div>
      <section className="mt-10 border-t border-card-border pt-8" aria-labelledby="foundation-status">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="foundation-status" className="text-base font-semibold text-text-primary">Foundation status</h2>
          <p className="text-sm text-text-tertiary">Account and workspace</p>
        </div>
        <dl className="mt-5 divide-y divide-card-border rounded-xl border border-card-border bg-card-background sm:grid sm:grid-cols-2 sm:divide-x sm:divide-y-0">
          <div className="px-5 py-4">
            <dt className="text-xs font-medium uppercase tracking-[0.08em] text-text-tertiary">Organization</dt>
            <dd className="mt-1.5 text-sm font-medium text-text-primary">{activeOrganization?.name ?? "Workspace connected"}</dd>
          </div>
          <div className="px-5 py-4">
            <dt className="text-xs font-medium uppercase tracking-[0.08em] text-text-tertiary">Access level</dt>
            <dd className="mt-1.5 text-sm font-medium capitalize text-text-primary">{activeOrganization?.role ?? "Member"}</dd>
          </div>
        </dl>
        <p className="mt-4 max-w-2xl text-sm leading-6 text-text-tertiary">Your authenticated organization context is connected. Location data and decision tools are intentionally not part of this foundation milestone.</p>
      </section>
    </div>
  );
}
