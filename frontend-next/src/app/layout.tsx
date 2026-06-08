import "./globals.css";
import ClientShell from "@/components/layout/client-shell";

export const metadata = {
  title: "青鳄量化 Pro",
  description: "AI量化研究实验室 · A股",
  icons: {
    icon: "/slogo.svg",
    shortcut: "/slogo.svg",
    apple: "/slogo.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="antialiased" style={{ backgroundColor: "#0B1220", color: "#E5E7EB" }}>
        <ClientShell>{children}</ClientShell>
      </body>
    </html>
  );
}
