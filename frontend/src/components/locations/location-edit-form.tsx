"use client";

import { SectionCard } from "@/components/common/section-card";
import {
  Alert,
  AlertContent,
  AlertDescription,
  AlertIndicator,
  AlertTitle,
} from "@/components/tailgrids/core/alert";
import { Button } from "@/components/tailgrids/core/button";
import {
  FieldDescription,
  FieldError,
  FieldLabel,
} from "@/components/tailgrids/core/field";
import { Input } from "@/components/tailgrids/core/input";
import { Spinner } from "@/components/tailgrids/core/spinner";
import { TextArea } from "@/components/tailgrids/core/text-area";
import { TextField } from "@/components/tailgrids/core/text-field";
import {
  useApplyLocationEditMutation,
  useLocationEditPreviewMutation,
} from "@/hooks/use-locations";
import { ApiError } from "@/services/api/client";
import type {
  FieldChange,
  LocationDetail,
  LocationEditRequest,
  LocationOpenStatus,
  ProfileAction,
} from "@/services/api/locations";
import { cn } from "@/utils/cn";
import { Buildings11, ClockThree } from "@tailgrids/icons";
import { useMemo, useState, type FormEvent } from "react";
import { Label, Radio, RadioGroup } from "react-aria-components";
import type { DraftHandoff } from "@/components/recommendations/draft-handoff";
import { EditPreviewDialog } from "./edit-preview-dialog";
import { editFieldLabel } from "./edit-fields";
import { HoursEditor } from "./hours-editor";
import {
  draftPeriodErrors,
  nonRegularPeriods,
  regularPeriods,
  toApiPeriods,
  toDraftPeriods,
  type HoursDraftPeriod,
} from "./hours-model";

const DESCRIPTION_MAX_LENGTH = 750;

const OPEN_STATUS_OPTIONS: {
  value: LocationOpenStatus;
  label: string;
  hint: string;
}[] = [
  { value: "open", label: "Open", hint: "Trading as normal" },
  {
    value: "closed_temporarily",
    label: "Temporarily closed",
    hint: "Reopening later",
  },
  {
    value: "closed_permanently",
    label: "Permanently closed",
    hint: "Will not reopen",
  },
];

export interface AppliedEdit {
  action: ProfileAction;
  changes: FieldChange[];
}

interface LocationEditFormProps {
  location: LocationDetail;
  /** A value drafted by the audit, prefilled into its field for review. */
  draft?: DraftHandoff | null;
  onCancel: () => void;
  onApplied: (result: AppliedEdit) => void;
}

function toNullable(value: string) {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

/**
 * The editable form for a Google Business Profile. Saving never writes straight
 * through: it dry-runs the edit, shows the API's own diff, and only the confirmation
 * in that dialog reaches the live listing.
 */
export function LocationEditForm({
  location,
  draft = null,
  onCancel,
  onApplied,
}: LocationEditFormProps) {
  const [title, setTitle] = useState(
    draft?.field === "title" ? draft.value : location.title,
  );
  const [phone, setPhone] = useState(location.phone_primary ?? "");
  const [website, setWebsite] = useState(location.website_uri ?? "");
  const [description, setDescription] = useState(
    draft?.field === "description" ? draft.value : (location.description ?? ""),
  );
  const [openStatus, setOpenStatus] = useState<LocationOpenStatus | null>(
    location.open_status,
  );
  const [periods, setPeriods] = useState<HoursDraftPeriod[]>(() =>
    toDraftPeriods(location.hours_periods),
  );

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  /**
   * The exact payload that was sent for preview. Confirming must apply this and not a
   * payload rebuilt later, so the diff the person approved is the diff Google gets.
   */
  const [reviewedRequest, setReviewedRequest] =
    useState<LocationEditRequest | null>(null);
  /** A response that succeeded as a request but came back as a failed action. */
  const [rejection, setRejection] = useState<ApiError | null>(null);

  const preview = useLocationEditPreviewMutation(location.id);
  const apply = useApplyLocationEditMutation(location.id);

  const preservedHours = useMemo(
    () => nonRegularPeriods(location.hours_periods),
    [location.hours_periods],
  );
  const hoursErrors = useMemo(() => draftPeriodErrors(periods), [periods]);
  const hadRegularHours = useMemo(
    () => regularPeriods(location.hours_periods).length > 0,
    [location.hours_periods],
  );

  /**
   * A profile with no regular week is "not set", which is a different instruction to
   * Google than "closed every day". Hours are only sent once there is a week to send.
   */
  const isHoursUnset = !hadRegularHours && periods.length === 0;

  const isBusy = preview.isPending || apply.isPending;

  const request: LocationEditRequest = {
    title: title.trim(),
    phone_primary: toNullable(phone),
    website_uri: toNullable(website),
    description: toNullable(description),
    ...(openStatus ? { open_status: openStatus } : {}),
    ...(isHoursUnset
      ? {}
      : { hours_periods: toApiPeriods(periods, preservedHours) }),
  };

  function clearFieldError(field: string) {
    setFieldErrors((current) => {
      if (!(field in current)) return current;
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  function validate(): Record<string, string> {
    const errors: Record<string, string> = {};

    if (!title.trim()) {
      errors.title = "Enter the business name Google should show.";
    }

    const site = website.trim();
    if (site && !/^https?:\/\/\S+$/i.test(site)) {
      errors.website_uri =
        "Enter a full web address, starting with http:// or https://.";
    }

    if (Object.keys(hoursErrors).length > 0) {
      errors.hours_periods =
        Object.keys(hoursErrors).length === 1
          ? "One opening hours period needs fixing before these changes can be reviewed."
          : `${Object.keys(hoursErrors).length} opening hours periods need fixing before these changes can be reviewed.`;
    }

    return errors;
  }

  function runPreview(payload: LocationEditRequest) {
    setRejection(null);
    apply.reset();
    preview.mutate(payload, {
      onSuccess: (data) => setFieldErrors(data.field_errors ?? {}),
    });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isBusy) return;

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setReviewedRequest(request);
    runPreview(request);
  }

  function handleConfirm() {
    if (!reviewedRequest) return;
    setRejection(null);
    apply.mutate(reviewedRequest, {
      onSuccess: (action) => {
        if (action.status === "failed") {
          setRejection(
            new ApiError(
              action.error ??
                "Google did not apply this change. No reason was returned.",
              502,
            ),
          );
          return;
        }
        setReviewedRequest(null);
        onApplied({ action, changes: preview.data?.changes ?? [] });
      },
    });
  }

  function handleBack() {
    if (apply.isPending) return;
    setReviewedRequest(null);
    setRejection(null);
    apply.reset();
  }

  const invalidFields = Object.keys(fieldErrors);

  return (
    <>
      <form
        onSubmit={handleSubmit}
        noValidate
        className="flex min-w-0 flex-col gap-5"
      >
        {draft ? (
          <Alert status="info" className="max-w-none">
            <AlertIndicator />
            <AlertContent>
              <AlertTitle>
                The audit&apos;s draft{" "}
                {draft.field === "title" ? "name" : "description"} is prefilled
                below
              </AlertTitle>
              <AlertDescription>
                {draft.reason ? `${draft.reason} ` : ""}Review it, change
                anything you like, then preview. Nothing reaches Google until
                you confirm the preview.
              </AlertDescription>
            </AlertContent>
          </Alert>
        ) : null}
        {invalidFields.length > 0 ? (
          <Alert status="error" className="max-w-none">
            <AlertIndicator />
            <AlertContent>
              <AlertTitle>
                {invalidFields.length === 1
                  ? "One field needs attention"
                  : `${invalidFields.length} fields need attention`}
              </AlertTitle>
              <AlertDescription>
                <ul className="space-y-1.5">
                  {invalidFields.map((field) => (
                    <li key={field}>
                      <span className="font-medium">
                        {editFieldLabel(field)}:
                      </span>{" "}
                      {fieldErrors[field]}
                    </li>
                  ))}
                </ul>
              </AlertDescription>
            </AlertContent>
          </Alert>
        ) : null}

        <SectionCard
          title="Business info"
          icon={<Buildings11 aria-hidden="true" focusable="false" />}
        >
          <div className="grid gap-5 sm:grid-cols-2">
            <TextField
              value={title}
              onChange={(value) => {
                setTitle(value);
                clearFieldError("title");
              }}
              validationBehavior="aria"
              invalid={Boolean(fieldErrors.title)}
              disabled={isBusy}
              required
              className="gap-1.5 sm:col-span-2"
            >
              <FieldLabel>Business name</FieldLabel>
              <Input
                autoFocus
                className="w-full"
                placeholder="The name customers see"
              />
              {fieldErrors.title ? (
                <FieldError>{fieldErrors.title}</FieldError>
              ) : null}
            </TextField>

            <TextField
              value={phone}
              onChange={(value) => {
                setPhone(value);
                clearFieldError("phone_primary");
              }}
              type="tel"
              validationBehavior="aria"
              invalid={Boolean(fieldErrors.phone_primary)}
              disabled={isBusy}
              className="gap-1.5"
            >
              <FieldLabel>Phone</FieldLabel>
              <Input
                className="w-full"
                autoComplete="tel"
                placeholder="+44 20 7946 0000"
              />
              {fieldErrors.phone_primary ? (
                <FieldError>{fieldErrors.phone_primary}</FieldError>
              ) : (
                <FieldDescription className="text-xs text-text-tertiary">
                  Leave empty to remove the phone number from Google.
                </FieldDescription>
              )}
            </TextField>

            <TextField
              value={website}
              onChange={(value) => {
                setWebsite(value);
                clearFieldError("website_uri");
              }}
              type="url"
              validationBehavior="aria"
              invalid={Boolean(fieldErrors.website_uri)}
              disabled={isBusy}
              className="gap-1.5"
            >
              <FieldLabel>Website</FieldLabel>
              <Input
                className="w-full"
                autoComplete="url"
                placeholder="https://example.com"
              />
              {fieldErrors.website_uri ? (
                <FieldError>{fieldErrors.website_uri}</FieldError>
              ) : (
                <FieldDescription className="text-xs text-text-tertiary">
                  Leave empty to remove the website from Google.
                </FieldDescription>
              )}
            </TextField>

            <TextField
              value={description}
              onChange={(value) => {
                setDescription(value);
                clearFieldError("description");
              }}
              validationBehavior="aria"
              invalid={Boolean(fieldErrors.description)}
              disabled={isBusy}
              className="gap-1.5 sm:col-span-2"
            >
              <FieldLabel>Description</FieldLabel>
              <TextArea
                rows={5}
                maxLength={DESCRIPTION_MAX_LENGTH}
                className="w-full"
                placeholder="What this business does, in the words you want on Google."
              />
              {fieldErrors.description ? (
                <FieldError>{fieldErrors.description}</FieldError>
              ) : (
                <FieldDescription className="text-xs text-text-tertiary tabular-nums">
                  {description.length} of {DESCRIPTION_MAX_LENGTH} characters
                </FieldDescription>
              )}
            </TextField>

            <RadioGroup
              value={openStatus ?? ""}
              onChange={(value) => {
                setOpenStatus(value as LocationOpenStatus);
                clearFieldError("open_status");
              }}
              isDisabled={isBusy}
              className="flex flex-col gap-1.5 sm:col-span-2"
            >
              <Label className="text-sm font-medium text-input-label-text select-none">
                Open status
              </Label>
              <div className="grid gap-2 sm:grid-cols-3">
                {OPEN_STATUS_OPTIONS.map((option) => (
                  <Radio
                    key={option.value}
                    value={option.value}
                    className={({ isSelected, isFocusVisible, isDisabled }) =>
                      cn(
                        "group flex min-h-11 cursor-pointer items-start gap-2.5 rounded-lg border px-3 py-2.5 transition",
                        isSelected
                          ? "border-button-primary-background bg-background-gray-secondary"
                          : "border-card-border hover:bg-background-gray-secondary",
                        isFocusVisible &&
                          "ring-4 ring-button-primary-focus-ring outline-none",
                        isDisabled && "cursor-not-allowed opacity-60",
                      )
                    }
                  >
                    <span
                      aria-hidden="true"
                      className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full border border-border-secondary-alt group-data-[selected]:border-button-primary-background group-data-[selected]:bg-button-primary-background"
                    >
                      <span className="size-1.5 rounded-full bg-white-100 opacity-0 group-data-[selected]:opacity-100" />
                    </span>
                    <span className="min-w-0">
                      <span className="block text-sm font-medium text-text-primary">
                        {option.label}
                      </span>
                      <span className="mt-0.5 block text-xs leading-5 text-text-tertiary">
                        {option.hint}
                      </span>
                    </span>
                  </Radio>
                ))}
              </div>
              {fieldErrors.open_status ? (
                <p className="text-sm text-input-error">
                  {fieldErrors.open_status}
                </p>
              ) : openStatus === null ? (
                <p className="text-xs text-text-tertiary">
                  This profile has no open status set. Choosing one sends it to
                  Google.
                </p>
              ) : null}
            </RadioGroup>
          </div>
        </SectionCard>

        <SectionCard
          title="Hours"
          icon={<ClockThree aria-hidden="true" focusable="false" />}
          bodyClassName="px-5 py-4"
        >
          <HoursEditor
            periods={periods}
            onChange={(next) => {
              setPeriods(next);
              clearFieldError("hours");
            }}
            errors={hoursErrors}
            fieldError={fieldErrors.hours_periods ?? null}
            preservedCount={preservedHours.length}
            isUnset={isHoursUnset}
            disabled={isBusy}
          />
        </SectionCard>

        <div className="sticky bottom-4 z-10 rounded-xl border border-card-border bg-card-background px-5 py-4 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs leading-5 text-text-tertiary">
              Nothing reaches Google until you review the changes and confirm
              them.
            </p>
            <div className="flex flex-wrap items-center gap-2.5">
              <Button
                type="button"
                variant="primary"
                appearance="outline"
                size="xl"
                onPress={onCancel}
                isDisabled={isBusy}
              >
                Cancel
              </Button>
              <Button type="submit" size="xl" isDisabled={isBusy}>
                {preview.isPending ? (
                  <span
                    aria-hidden="true"
                    className="flex size-5 shrink-0 items-center justify-center"
                  >
                    <Spinner size="sm" className="size-5" />
                  </span>
                ) : null}
                {preview.isPending ? "Checking with Google…" : "Review changes"}
              </Button>
            </div>
          </div>
        </div>
      </form>

      {reviewedRequest ? (
        <EditPreviewDialog
          locationTitle={location.title}
          preview={preview.data ?? null}
          isLoadingPreview={preview.isPending}
          previewError={preview.error}
          isApplying={apply.isPending}
          applyError={apply.error ?? rejection}
          onRetryPreview={() => runPreview(reviewedRequest)}
          onBack={handleBack}
          onConfirm={handleConfirm}
        />
      ) : null}
    </>
  );
}
