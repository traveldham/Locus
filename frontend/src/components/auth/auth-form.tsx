"use client";

import { Button } from "@/components/tailgrids/core/button";
import { FieldError, FieldLabel } from "@/components/tailgrids/core/field";
import { Input } from "@/components/tailgrids/core/input";
import { TextField } from "@/components/tailgrids/core/text-field";
import { useAuth } from "@/contexts/auth-context";
import { FormEvent, useState } from "react";
import { DEMO_ACCOUNT } from "./demo-account";

export function AuthForm({ nextPath = "/" }: { nextPath?: string }) {
  const { login } = useAuth();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    const data = new FormData(event.currentTarget);
    try {
      await login(String(data.get("email")), String(data.get("password")), nextPath);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "We could not complete that request.");
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <TextField name="email" type="email" required defaultValue={DEMO_ACCOUNT.email} className="gap-1.5">
        <FieldLabel>Work email</FieldLabel>
        <Input autoComplete="email" className="w-full" placeholder="you@company.com" />
      </TextField>
      <TextField
        name="password"
        type="password"
        required
        minLength={8}
        defaultValue={DEMO_ACCOUNT.password}
        className="gap-1.5"
      >
        <FieldLabel>Password</FieldLabel>
        <Input autoComplete="current-password" className="w-full" />
        <FieldError />
      </TextField>
      {error && <p role="alert" className="rounded-lg bg-background-soft-100 px-3 py-2 text-sm text-error-500">{error}</p>}
      <Button type="submit" size="xl" isDisabled={isSubmitting} className="w-full">
        {isSubmitting ? "Please wait…" : "Sign in"}
      </Button>
    </form>
  );
}
