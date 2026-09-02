import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Shell } from "@/components/Shell";

export const metadata: Metadata = {
  title: "SlopeSense NER",
  description: "Landslide early warning for India's North Eastern Region",
  manifest: "/manifest.json",
  appleWebApp: { capable: true, title: "SlopeSense NER" },
};

export const viewport: Viewport = {
  themeColor: "#2f4a38",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=Source+Serif+4:opsz,wght@8..60,600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Shell>{children}</Shell>
        <script
          dangerouslySetInnerHTML={{
            __html: `if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js'));}`,
          }}
        />
      </body>
    </html>
  );
}
