import { redirect } from "next/navigation";

// There is no separate dashboard: the organization context it used to show now lives in
// the header, so the root lands straight on the locations the workspace is about.
export default function Home() {
  redirect("/locations");
}
