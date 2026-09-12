"use client";

import {
  Alert,
  AlertContent,
  AlertDescription,
  AlertIndicator,
  AlertTitle,
} from "@/components/tailgrids/core/alert";
import { Button } from "@/components/tailgrids/core/button";

interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
}

export function ErrorState({
  title = "We could not load this",
  description = "The request to Locus did not complete. Check your connection, then try again.",
  onRetry,
  isRetrying = false,
}: ErrorStateProps) {
  return (
    <Alert status="error" className="max-w-none">
      <AlertIndicator />
      <AlertContent>
        <AlertTitle>{title}</AlertTitle>
        <AlertDescription>{description}</AlertDescription>
        {onRetry ? (
          <Button
            size="xl"
            variant="danger"
            appearance="outline"
            onPress={onRetry}
            isDisabled={isRetrying}
          >
            {isRetrying ? "Retrying…" : "Try again"}
          </Button>
        ) : null}
      </AlertContent>
    </Alert>
  );
}
