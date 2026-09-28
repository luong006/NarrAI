import type { Metadata } from "next";
import { ThemeProvider } from "@/components/theme-provider";
import { ToastProvider } from "@/lib/toast";
import { ToastContainer } from "@/components/ui/Toast";
import "./globals.css";

export const metadata: Metadata = {
  title: "NarrAI - AI Novel & Manga Co-creation Workspace",
  description: "Transform your narrative ideas into rich novels and authentic black & white manga with artificial intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className="bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 min-h-screen">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <ToastProvider>
            {children}
            <ToastContainer />
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
