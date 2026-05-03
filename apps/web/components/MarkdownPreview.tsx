"use client";

import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

type Props = {
  markdown: string;
};

export function MarkdownPreview({ markdown }: Props) {
  return (
    <div className="max-w-none space-y-3 text-sm leading-relaxed text-slate-200 [&_a]:text-mineru-accent [&_code]:rounded [&_code]:bg-black/30 [&_code]:px-1 [&_h1]:text-xl [&_h2]:text-lg [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-black/40 [&_pre]:p-3">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
