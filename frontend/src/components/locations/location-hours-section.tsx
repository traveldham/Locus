"use client";

import { SectionCard } from "@/components/common/section-card";
import type { LocationHoursPeriod } from "@/services/api/locations";
import { ClockThree } from "@tailgrids/icons";
import type { ReactNode } from "react";
import {
  WEEK_DAYS,
  dayLabel,
  describePeriod,
  humanizeToken,
  normalizeToken,
} from "./hours-model";

interface HoursGroup {
  hoursType: string;
  label: string;
  isRegular: boolean;
  days: { day: string; label: string; periods: string[] }[];
}

function buildGroups(hours: LocationHoursPeriod[]): HoursGroup[] {
  const byType = new Map<string, LocationHoursPeriod[]>();
  for (const period of hours) {
    const type = normalizeToken(period.hours_type) || "REGULAR";
    const bucket = byType.get(type);
    if (bucket) bucket.push(period);
    else byType.set(type, [period]);
  }

  const types = [...byType.keys()].sort((a, b) => {
    if (a === "REGULAR") return -1;
    if (b === "REGULAR") return 1;
    return a.localeCompare(b);
  });

  return types.map((hoursType) => {
    const periods = byType.get(hoursType) ?? [];
    const isRegular = hoursType === "REGULAR";

    const byDay = new Map<string, string[]>();
    for (const period of periods) {
      const day = normalizeToken(period.open_day);
      const bucket = byDay.get(day);
      if (bucket) bucket.push(describePeriod(period));
      else byDay.set(day, [describePeriod(period)]);
    }

    const knownDays = [
      ...WEEK_DAYS,
      ...[...byDay.keys()].filter(
        (day) => !WEEK_DAYS.includes(day as (typeof WEEK_DAYS)[number]),
      ),
    ];
    // Regular hours always list every weekday, because a day with no period is closed.
    // Other hour types only list the days they actually cover.
    const orderedDays = isRegular ? knownDays : knownDays.filter((day) => byDay.has(day));

    return {
      hoursType,
      label: isRegular ? "Regular hours" : humanizeToken(hoursType),
      isRegular,
      days: orderedDays.map((day) => ({
        day,
        label: dayLabel(day),
        periods: byDay.get(day) ?? [],
      })),
    };
  });
}

interface LocationHoursSectionProps {
  hours: LocationHoursPeriod[];
  actions?: ReactNode;
}

export function LocationHoursSection({ hours, actions }: LocationHoursSectionProps) {
  const groups = buildGroups(hours);

  return (
    <SectionCard
      title="Hours"
      icon={<ClockThree aria-hidden="true" focusable="false" />}
      actions={actions}
      bodyClassName="px-5 py-4"
    >
      {groups.length === 0 ? (
        <p className="text-sm leading-6 text-text-tertiary">
          No opening hours are set on this Google profile.
        </p>
      ) : (
        <div className="space-y-6">
          {groups.map((group) => (
            <div key={group.hoursType}>
              {groups.length > 1 || !group.isRegular ? (
                <h3 className="mb-2.5 text-[11px] font-medium tracking-[0.08em] text-text-tertiary uppercase">
                  {group.label}
                </h3>
              ) : null}
              <dl className="divide-y divide-card-border">
                {group.days.map((day) => (
                  <div
                    key={day.day}
                    className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-0.5 py-2.5 first:pt-0 last:pb-0"
                  >
                    <dt className="text-sm font-medium text-text-primary">{day.label}</dt>
                    <dd className="text-right text-sm text-text-secondary">
                      {day.periods.length === 0 ? (
                        <span className="text-text-disable">Closed</span>
                      ) : (
                        day.periods.map((period, index) => (
                          <span key={`${day.day}-${index}`} className="block tabular-nums">
                            {period}
                          </span>
                        ))
                      )}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          ))}
        </div>
      )}
    </SectionCard>
  );
}
