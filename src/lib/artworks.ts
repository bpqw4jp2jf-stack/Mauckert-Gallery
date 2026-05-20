import artworksData from "../../data/artworks.json";
import categoriesData from "../../data/categories.json";

export interface ArtworkMedia {
  id: string;
  title: string | null;
  width: number | null;
  height: number | null;
  original_url: string;
  display_url: string;
  local_path?: string;
}

export interface Artwork {
  slug: string;
  name: string;
  description: string;
  price: number | null;
  currency: string;
  formatted_price: string | null;
  category_ids: string[];
  categories: string[];
  category_slugs: string[];
  in_stock: boolean;
  media: ArtworkMedia[];
  source_url: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
}

export const artworks: Artwork[] = artworksData as Artwork[];
export const categories: Category[] = categoriesData as Category[];

export function artworksByCategorySlug(slug: string): Artwork[] {
  return artworks.filter((a) => a.category_slugs.includes(slug));
}

export function getArtworkBySlug(slug: string): Artwork | undefined {
  return artworks.find((a) => a.slug === slug);
}

export function primaryImage(a: Artwork): string {
  const m = a.media[0];
  if (!m) return "";
  return m.local_path || m.display_url;
}

export function formatPrice(a: Artwork): string {
  if (a.formatted_price) return a.formatted_price;
  if (a.price == null) return "Preis auf Anfrage";
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: a.currency || "EUR",
    maximumFractionDigits: 0,
  }).format(a.price);
}
