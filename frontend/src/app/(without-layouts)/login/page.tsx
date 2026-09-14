import { AuthForm } from "@/components/auth/auth-form";
import { AuthShell } from "@/components/auth/auth-shell";
import { DEMO_ACCOUNT } from "@/components/auth/demo-account";
import {
  Alert,
  AlertContent,
  AlertDescription,
  AlertIndicator,
  AlertTitle,
} from "@/components/tailgrids/core/alert";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Sign in" };

function safeNextPath(value: string | string[] | undefined) {
  const path = Array.isArray(value) ? value[0] : value;
  return path?.startsWith("/") && !path.startsWith("//") ? path : "/";
}

function CredentialRow({ term, value }: { term: string; value: string }) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-2">
      <dt className="w-20 shrink-0 text-text-tertiary">{term}</dt>
      <dd className="font-mono text-sm break-all text-text-primary select-all">{value}</dd>
    </div>
  );
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string | string[] }>;
}) {
  const nextPath = safeNextPath((await searchParams).next);

  return (
    <AuthShell title="Welcome back" description="Sign in to continue to your organization workspace.">
      <Alert status="info" className="mt-8 max-w-none">
        <AlertIndicator />
        <AlertContent>
          <AlertTitle>Demo account</AlertTitle>
          <AlertDescription>
            This build ships with one seeded account, already signed up and already holding the
            sample profile data. The fields below are prefilled with it.
          </AlertDescription>
          <dl className="w-full space-y-1 text-sm leading-6">
            <CredentialRow term="Email" value={DEMO_ACCOUNT.email} />
            <CredentialRow term="Password" value={DEMO_ACCOUNT.password} />
          </dl>
        </AlertContent>
      </Alert>

      <div className="mt-8">
        <AuthForm nextPath={nextPath} />
      </div>
    </AuthShell>
  );
}
