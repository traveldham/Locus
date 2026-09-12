import { HomeIcon } from "./icon";

interface NavigationItem {
  title: string;
  icon: React.ReactNode;
  url?: string;
  items: Array<{ title: string; url?: string }>;
}

interface NavigationSection {
  label: string;
  items: NavigationItem[];
}

export const NAV_DATA: NavigationSection[] = [
  {
    label: "WORKSPACE",
    items: [
      {
        title: "Dashboard",
        icon: <HomeIcon />,
        url: "/",
        items: [],
      },
    ],
  },
];
