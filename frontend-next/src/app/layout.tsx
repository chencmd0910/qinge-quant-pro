import "./globals.css";

export const metadata = {
  title: "青鳄量化 Pro - AI Quant OS",
  description: "AI量化研究实验室",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="bg-slate-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
