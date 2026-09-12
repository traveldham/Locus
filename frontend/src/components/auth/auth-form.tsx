"use client";

import { Button } from "@/components/tailgrids/core/button";
import { FieldError, FieldLabel } from "@/components/tailgrids/core/field";
import { Input } from "@/components/tailgrids/core/input";
import { TextField } from "@/components/tailgrids/core/text-field";
import { useAuth } from "@/contexts/auth-context";
import Link from "next/link";
import { FormEvent, useState } from "react";

export function AuthForm({ mode, nextPath = "/" }: { mode: "login" | "register"; nextPath?: string }) {
  const { login, register } = useAuth();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    const data = new FormData(event.currentTarget);
    try {
      if (mode === "login") {
        await login(String(data.get("email")), String(data.get("password")), nextPath);
      }
      else await register({
        full_name: String(data.get("full_name")),
        organization_name: String(data.get("organization_name")),
        email: String(data.get("email")),
        password: String(data.get("password")),
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "We could not complete that request.");
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-8 space-y-5">
      {mode === "register" && <>
        <TextField name="full_name" required className="gap-1.5"><FieldLabel>Full name</FieldLabel><Input autoComplete="name" className="w-full" /></TextField>
        <TextField name="organization_name" required className="gap-1.5"><FieldLabel>Organization</FieldLabel><Input autoComplete="organization" className="w-full" /></TextField>
      </>}
      <TextField name="email" type="email" required className="gap-1.5"><FieldLabel>Work email</FieldLabel><Input autoComplete="email" className="w-full" placeholder="you@company.com" /></TextField>
      <TextField name="password" type="password" required minLength={8} className="gap-1.5"><FieldLabel>Password</FieldLabel><Input autoComplete={mode === "login" ? "current-password" : "new-password"} className="w-full" /><FieldError /></TextField>
      {error && <p role="alert" className="rounded-lg bg-background-soft-100 px-3 py-2 text-sm text-error-500">{error}</p>}
      <Button type="submit" size="xl" isDisabled={isSubmitting} className="w-full">
        {isSubmitting ? "Please wait…" : mode === "login" ? "Sign in" : "Create workspace"}
      </Button>
      <p className="text-center text-sm text-text-tertiary">
        {mode === "login" ? "New to Locus?" : "Already have an account?"}{" "}
        <Link href={mode === "login" ? "/register" : "/login"} className="font-medium text-text-primary underline decoration-border-primary underline-offset-4">
          {mode === "login" ? "Create an account" : "Sign in"}
        </Link>
      </p>
    </form>
  );
}
