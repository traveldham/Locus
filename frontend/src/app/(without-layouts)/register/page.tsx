import { AuthForm } from "@/components/auth/auth-form";
import { AuthShell } from "@/components/auth/auth-shell";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Create account" };

export default function RegisterPage() {
  return <AuthShell title="Create your workspace" description="Set up your organization and the first administrator account."><AuthForm mode="register" /></AuthShell>;
}
