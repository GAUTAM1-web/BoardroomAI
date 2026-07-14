import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Providers } from "@/app/providers";
import { APP_NAME, APP_VERSION } from "@/lib/app-config";
import "./globals.css";

export const metadata: Metadata = {
  title: APP_NAME,
  description: "Executive AI operating system for founders.",
  applicationName: APP_NAME,
  generator: `${APP_NAME} ${APP_VERSION}`
};

export default function RootLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
