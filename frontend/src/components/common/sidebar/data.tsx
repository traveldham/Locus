import {
  BookingsIcon,
  CompetitorsIcon,
  InsightsIcon,
  LocationsIcon,
  PostsIcon,
  RankingsIcon,
  ReviewsIcon,
} from "./icon";

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

// Sections mirror where the data comes from: everything under INSIGHTS is reported by
// Google, everything under MARKET is not and never will be — see tasks/016.
export const NAV_DATA: NavigationSection[] = [
  {
    label: "WORKSPACE",
    items: [
      {
        title: "Location audit",
        icon: <InsightsIcon />,
        url: "/recommendations",
        items: [],
      },
      {
        title: "Locations",
        icon: <LocationsIcon />,
        url: "/locations",
        items: [],
      },
      { title: "Reviews", icon: <ReviewsIcon />, url: "/reviews", items: [] },
      { title: "Posts", icon: <PostsIcon />, url: "/posts", items: [] },
      // One entry: performance, search terms and photos are tabs inside the page.
      {
        title: "Insights",
        icon: <InsightsIcon />,
        url: "/insights",
        items: [],
      },
    ],
  },
  {
    label: "MARKET",
    items: [
      {
        title: "Rankings",
        icon: <RankingsIcon />,
        url: "/market/rankings",
        items: [],
      },
      {
        title: "Competitors",
        icon: <CompetitorsIcon />,
        url: "/market/competitors",
        items: [],
      },
      {
        title: "Bookings",
        icon: <BookingsIcon />,
        url: "/bookings",
        items: [],
      },
    ],
  },
];
