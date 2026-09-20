import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FridgeGuard | Gainesville Community Fridge",
  description:
    "Live temperature, door, and connection monitoring for the Gainesville Community Fridge.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
