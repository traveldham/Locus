"use client";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { SourceMark } from "@/components/common/source-mark";
import { Button } from "@/components/tailgrids/core/button";
import {
  Select,
  SelectContent,
  SelectIndicator,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/tailgrids/core/select";
import { useLocationsQuery } from "@/hooks/use-locations";
import { usePostsQuery } from "@/hooks/use-posts";
import { POSTS_PAGE_SIZE, type PostType } from "@/services/api/posts";
import { formatDate } from "@/utils/format-date";
import { FileText } from "@tailgrids/icons";
import Link from "next/link";
import { useState } from "react";

const TYPES: PostType[] = ["standard", "event", "offer", "alert"];
const ANY_LOCATION = "__any_location__";
const ANY_TYPE = "__any_type__";
const label = (value: string) => value.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());

export function PostsView() {
  const [locationId, setLocationId] = useState<string | undefined>();
  const [postType, setPostType] = useState<PostType | undefined>();
  const [offset, setOffset] = useState(0);
  const locations = useLocationsQuery();
  const posts = usePostsQuery({ locationId, postType, limit: POSTS_PAGE_SIZE, offset });
  const items = posts.data?.items ?? [];

  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <PageHeader
        title="Posts"
        description="Published updates, events and offers across every Google Business Profile."
        meta={posts.data ? <SourceMark source={posts.data.source} /> : null}
      />

      <div className="mt-6 flex flex-wrap gap-3 rounded-xl border border-card-border bg-card-background p-4">
        <Select
          aria-label="Filter posts by location"
          value={locationId ?? ANY_LOCATION}
          onChange={(key: string) => { setLocationId(key === ANY_LOCATION ? undefined : key); setOffset(0); }}
          className="min-w-56"
        >
          <SelectTrigger size="xl"><SelectValue /><SelectIndicator /></SelectTrigger>
          <SelectContent className="max-h-72">
            <SelectItem id={ANY_LOCATION}>All locations</SelectItem>
            {(locations.data ?? []).map((location) => (
              <SelectItem key={location.id} id={location.id}>{location.title}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          aria-label="Filter posts by type"
          value={postType ?? ANY_TYPE}
          onChange={(key: string) => { setPostType(key === ANY_TYPE ? undefined : key as PostType); setOffset(0); }}
          className="min-w-48"
        >
          <SelectTrigger size="xl"><SelectValue /><SelectIndicator /></SelectTrigger>
          <SelectContent>
            <SelectItem id={ANY_TYPE}>All post types</SelectItem>
            {TYPES.map((type) => <SelectItem key={type} id={type}>{label(type)}</SelectItem>)}
          </SelectContent>
        </Select>
        {(locationId || postType) ? (
          <Button appearance="outline" size="xl" onPress={() => { setLocationId(undefined); setPostType(undefined); setOffset(0); }}>
            Clear filters
          </Button>
        ) : null}
      </div>

      <div className="mt-5">
        {posts.isPending ? <p role="status" className="text-sm text-text-tertiary">Loading posts…</p> : null}
        {posts.isError ? <ErrorState title="We could not load posts" onRetry={() => void posts.refetch()} isRetrying={posts.isFetching} /> : null}
        {!posts.isPending && !posts.isError && items.length === 0 ? (
          <EmptyState icon={<FileText aria-hidden="true" />} title="No posts found" description="No published post matches the selected location and type." />
        ) : null}
        {items.length > 0 ? (
          <div className="grid gap-4 xl:grid-cols-2" aria-busy={posts.isFetching}>
            {items.map((post) => (
              <article key={post.id} className="rounded-xl border border-card-border bg-card-background p-5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-background-gray-secondary px-2.5 py-1 text-xs font-medium text-text-secondary">{label(post.post_type)}</span>
                  {post.cta_type ? <span className="rounded-full bg-badge-success-background px-2.5 py-1 text-xs font-medium text-badge-success-text">CTA: {label(post.cta_type)}</span> : null}
                  <time className="ml-auto text-xs text-text-tertiary" dateTime={post.published_on ?? undefined}>{formatDate(post.published_on) ?? "Date unavailable"}</time>
                </div>
                <p className="mt-4 text-sm leading-6 whitespace-pre-line text-text-primary">{post.summary ?? "No post text."}</p>
                <div className="mt-5 flex items-center justify-between gap-3 border-t border-card-border pt-3 text-xs text-text-tertiary">
                  <Link className="font-medium text-text-secondary hover:text-text-primary hover:underline" href={`/locations/${post.location_id}`}>{post.location_title ?? "Unknown location"}</Link>
                  <span title={post.google_post_id} className="max-w-44 truncate tabular-nums">{post.google_post_id}</span>
                </div>
              </article>
            ))}
          </div>
        ) : null}
        {posts.data && posts.data.total > POSTS_PAGE_SIZE ? (
          <div className="mt-5 flex items-center justify-between gap-4 text-sm text-text-secondary">
            <span>Showing {offset + 1}–{Math.min(offset + items.length, posts.data.total)} of {posts.data.total}</span>
            <div className="flex gap-2">
              <Button appearance="outline" size="xl" isDisabled={offset === 0} onPress={() => setOffset(Math.max(0, offset - POSTS_PAGE_SIZE))}>Previous</Button>
              <Button appearance="outline" size="xl" isDisabled={offset + POSTS_PAGE_SIZE >= posts.data.total} onPress={() => setOffset(offset + POSTS_PAGE_SIZE)}>Next</Button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
