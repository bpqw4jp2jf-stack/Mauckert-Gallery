import data from "../../data/exhibitions.json";

export interface PressInfo {
  outlet: string;
  headline: string;
  byline: string;
  date_label: string;
  quote: string;
  body: string[];
}

export interface Exhibition {
  slug: string;
  title: string;
  subtitle: string;
  location: string;
  date_label: string;
  start: string;
  end: string | null;
  status: "current" | "past";
  is_upcoming: boolean;
  description: string;
  press?: PressInfo;
  images: string[];
  cover: string | null;
}

export const exhibitions: Exhibition[] = data as Exhibition[];

export function upcoming(): Exhibition | undefined {
  return exhibitions.find((e) => e.is_upcoming);
}

export function past(): Exhibition[] {
  return exhibitions.filter((e) => !e.is_upcoming);
}

export function getExhibition(slug: string): Exhibition | undefined {
  return exhibitions.find((e) => e.slug === slug);
}
