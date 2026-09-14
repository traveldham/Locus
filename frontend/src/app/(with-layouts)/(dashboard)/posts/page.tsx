import { PostsView } from "@/components/posts/posts-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Posts",
  description: "Published posts across every Google Business Profile.",
};

export default function PostsPage() {
  return <PostsView />;
}
