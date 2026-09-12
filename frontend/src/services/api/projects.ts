import { apiRequest } from "./client";
import type { LocationSummary } from "./locations";

export type ProjectStatus = "active" | "archived";

export interface Project {
  id: string;
  name: string;
  slug: string;
  status: ProjectStatus;
  location_count: number;
  created_at: string;
}

export interface ProjectDetail extends Project {
  locations: LocationSummary[];
}

export interface CreateProjectInput {
  name: string;
  /** Optional when the locations were already imported into the organization. */
  google_connection_id?: string;
  location_ids?: string[];
}

/** A rename leaves the slug untouched on the API side. */
export interface UpdateProjectInput {
  name?: string;
  status?: ProjectStatus;
}

export interface ProjectListParams {
  status?: ProjectStatus;
}

/** The delete endpoints answer 200 with this body rather than 204 No Content. */
export interface MessageResponse {
  message: string;
}

function projectPath(id: string) {
  return `/projects/${encodeURIComponent(id)}`;
}

export const projectsApi = {
  list: ({ status }: ProjectListParams = {}) => {
    const query = new URLSearchParams();
    if (status) query.set("status", status);
    const search = query.toString();
    return apiRequest<Project[]>(`/projects${search ? `?${search}` : ""}`);
  },
  create: (input: CreateProjectInput) =>
    apiRequest<Project>("/projects", { method: "POST", body: JSON.stringify(input) }),
  get: (id: string) => apiRequest<ProjectDetail>(projectPath(id)),
  update: (id: string, input: UpdateProjectInput) =>
    apiRequest<Project>(projectPath(id), { method: "PATCH", body: JSON.stringify(input) }),
  remove: (id: string) => apiRequest<MessageResponse>(projectPath(id), { method: "DELETE" }),
  /** Returns the whole project with its locations, so the view can be refreshed from it. */
  addLocations: (id: string, locationIds: string[]) =>
    apiRequest<ProjectDetail>(`${projectPath(id)}/locations`, {
      method: "POST",
      body: JSON.stringify({ location_ids: locationIds }),
    }),
  removeLocation: (id: string, locationId: string) =>
    apiRequest<MessageResponse>(
      `${projectPath(id)}/locations/${encodeURIComponent(locationId)}`,
      { method: "DELETE" },
    ),
};
