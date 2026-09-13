"use client";

export interface BusinessDraft {
  website: string;
  description: string;
  services: string;
}

export const emptyBusiness: BusinessDraft = {
  website: "",
  description: "",
  services: "",
};

export function businessPayload(draft: BusinessDraft) {
  return {
    website_url: draft.website.trim() || null,
    description: draft.description.trim() || null,
    services: [
      ...new Set(
        draft.services
          .split("\n")
          .map((service) => service.trim())
          .filter(Boolean),
      ),
    ],
  };
}

export function BusinessFields({
  value,
  onChange,
  disabled = false,
}: {
  value: BusinessDraft;
  onChange: (value: BusinessDraft) => void;
  disabled?: boolean;
}) {
  const control =
    "mt-2 min-h-11 w-full rounded-lg border border-card-border bg-card-background px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus-visible:outline-2 focus-visible:outline-primary-500 disabled:opacity-50";
  return (
    <fieldset disabled={disabled} className="mt-5 space-y-4">
      <legend className="sr-only">Business details</legend>
      <label className="block text-sm font-medium text-text-primary">
        Website URL
        <input
          type="url"
          maxLength={2083}
          value={value.website}
          placeholder="https://example.com"
          onChange={(event) =>
            onChange({ ...value, website: event.target.value })
          }
          className={control}
        />
      </label>
      <label className="block text-sm font-medium text-text-primary">
        Services
        <textarea
          rows={3}
          maxLength={12100}
          value={value.services}
          placeholder={"General dentistry\nOrthodontics"}
          onChange={(event) =>
            onChange({ ...value, services: event.target.value })
          }
          className={control}
        />
        <span className="mt-1 block text-xs font-normal text-text-secondary">
          One service per line. Up to 100 services, 120 characters each.
        </span>
      </label>
      <label className="block text-sm font-medium text-text-primary">
        Business description
        <textarea
          rows={3}
          maxLength={5000}
          value={value.description}
          placeholder="Describe what the business does."
          onChange={(event) =>
            onChange({ ...value, description: event.target.value })
          }
          className={control}
        />
      </label>
      <p className="text-xs text-text-secondary">
        These details describe the business as a whole. You can update them
        later.
      </p>
    </fieldset>
  );
}
