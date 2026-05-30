"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function BlogProse({ markdown }: { markdown: string }) {
  return (
    <div className="prose prose-invert max-w-none prose-headings:font-semibold prose-headings:tracking-tight prose-h2:text-2xl prose-h2:mt-10 prose-h3:text-xl prose-a:text-secondary prose-strong:text-foreground prose-li:marker:text-secondary prose-hr:border-white/10">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
    </div>
  );
}
