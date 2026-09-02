"use client";

import dynamic from "next/dynamic";

const MapView = dynamic(() => import("@/components/MapView").then((m) => m.MapView), { ssr: false });

export default function MapPage() {
  return <MapView />;
}
