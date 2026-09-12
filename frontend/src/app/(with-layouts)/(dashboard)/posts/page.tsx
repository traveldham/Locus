import { PostsView } from "@/components/posts/posts-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Posts",
  description: "Published Google Business Profile posts across every location.",
};

export default function PostsPage() {
  return <PostsView />;
}
