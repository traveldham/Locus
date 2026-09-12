import { AuthForm } from "@/components/auth/auth-form";
import { AuthShell } from "@/components/auth/auth-shell";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Sign in" };

function safeNextPath(value: string | string[] | undefined) {
  const path = Array.isArray(value) ? value[0] : value;
  return path?.startsWith("/") && !path.startsWith("//") ? path : "/";
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string | string[] }>;
}) {
  const nextPath = safeNextPath((await searchParams).next);

  return (
    <AuthShell title="Welcome back" description="Sign in to continue to your organization workspace.">
      <AuthForm mode="login" nextPath={nextPath} />
    </AuthShell>
  );
}
