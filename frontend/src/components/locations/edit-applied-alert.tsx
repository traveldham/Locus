"use client";

import {
  Alert,
  AlertContent,
  AlertDescription,
  AlertIndicator,
  AlertTitle,
} from "@/components/tailgrids/core/alert";
import { Button } from "@/components/tailgrids/core/button";
import { describeChangeValue } from "./change-format";
import type { AppliedEdit } from "./location-edit-form";

/**
 * What actually happened after a confirmation. Google applies an edit
 * asynchronously, so the copy follows the status the API returned rather than
 * claiming the listing is already updated.
 */
export function EditAppliedAlert({
  result,
  onDismiss,
}: {
  result: AppliedEdit;
  onDismiss: () => void;
}) {
  const isLive = result.action.status === "succeeded";
  const count = result.changes.length;
  const countLabel = count === 1 ? "1 change" : `${count} changes`;

  return (
    <Alert status={isLive ? "success" : "info"} className="max-w-none">
      <AlertIndicator />
      <AlertContent>
        <AlertTitle>{isLive ? "Your changes are live on Google" : "Sent to Google"}</AlertTitle>
        <AlertDescription>
          {isLive
            ? `Google applied ${countLabel} to this profile.`
            : `${countLabel} went to Google and are waiting to be applied. Change history below shows the outcome.`}
          {count > 0 ? (
            <ul className="mt-2 space-y-1">
              {result.changes.map((change) => (
                <li key={change.field}>
                  <span className="font-medium">{change.label}:</span>{" "}
                  <span className="break-words whitespace-pre-line">
                    {describeChangeValue(change.proposed) ?? "Cleared"}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </AlertDescription>
        <Button
          type="button"
          size="xl"
          variant={isLive ? "success" : "primary"}
          appearance="outline"
          onPress={onDismiss}
        >
          Dismiss
        </Button>
      </AlertContent>
    </Alert>
  );
}
