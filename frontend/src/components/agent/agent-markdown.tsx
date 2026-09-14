"use client";

import { cn } from "@/utils/cn";
import { memo, type ReactNode } from "react";
import Markdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * The agent's prose, rendered as rich text.
 *
 * Everything this renders is untrusted. The model writes it, but what the model writes is
 * drawn from review text written by members of the public, so a reply can carry anything a
 * stranger chose to type into Google. Three things keep that safe, and none of them may be
 * relaxed without a reason better than "the markdown looked nicer":
 *
 * 1. **No raw HTML, ever.** `rehype-raw` is the plugin that turns HTML in the source into
 *    real elements, and it is deliberately not installed. Without it react-markdown never
 *    puts a `raw` node in the tree and never reaches for `dangerouslySetInnerHTML`;
 *    `skipHtml` then drops the passage rather than printing its angle brackets at the
 *    reader. Raw HTML is not escaped-and-shown, it is gone.
 * 2. **An allowlist, not a blocklist.** Only the elements below can be produced. An element
 *    a future plugin or a future markdown feature might introduce cannot appear by default,
 *    it has to be added here on purpose. `unwrapDisallowed` keeps the words inside anything
 *    that is filtered out, so filtering costs presentation and never content.
 * 3. **No URL is trusted and nothing is fetched.** `safeUrl` rejects every scheme except
 *    http, https and mailto, and rejects every attribute except `href` — which means no
 *    image, video or stylesheet is ever requested from an address a reviewer chose. `img`
 *    is off the allowlist as well, so there is nothing to fetch from in the first place.
 *
 * The styling is deliberately restrained. This renders inside a chat bubble a few hundred
 * pixels wide, not into an article: headings are barely larger than the body, blocks are
 * spaced in tenths of a line, and anything that could push the bubble wider than the panel
 * — a code block, a table — scrolls inside its own box instead.
 */

/**
 * Every element this renderer can produce. `img` is absent on purpose, and so is every
 * element that only raw HTML could have introduced.
 *
 * `input` is here for GFM task lists, which `mdast-util-to-hast` emits already disabled.
 */
const ALLOWED_ELEMENTS = [
  "p",
  "br",
  "strong",
  "em",
  "del",
  "a",
  "code",
  "pre",
  "ul",
  "ol",
  "li",
  "input",
  "blockquote",
  "hr",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "table",
  "thead",
  "tbody",
  "tr",
  "th",
  "td",
];

/** The only schemes a link in model output may point at. */
const SAFE_PROTOCOLS = new Set(["http:", "https:", "mailto:"]);

/**
 * What every URL in the source is put through before it reaches the DOM.
 *
 * Only `href` survives at all: every other URL attribute — `src` above all — is a request
 * the browser would make on the reader's behalf to an address chosen by whoever wrote the
 * review, so those are emptied whatever they contain.
 *
 * The scheme is read with the URL parser rather than matched with a regular expression,
 * because the parser is the thing the browser will agree with: it strips the tabs and
 * newlines that let `java&#9;script:` slip past a naive test, and it lower-cases and trims
 * the scheme the same way the navigation will.
 */
function safeUrl(url: string, key: string): string {
  if (key !== "href") return "";
  try {
    // The base only exists so relative links parse; the parsed URL is inspected and then
    // thrown away, and the original string is what gets rendered.
    const protocol = new URL(url, "https://locus.invalid").protocol;
    return SAFE_PROTOCOLS.has(protocol) ? url : "";
  } catch {
    return "";
  }
}

/** Shared by every block, so the bubble's own padding is not doubled at either end. */
const BLOCK = "my-2 first:mt-0 last:mb-0";

const COMPONENTS: Components = {
  p: ({ children }) => <p className={BLOCK}>{children}</p>,
  strong: ({ children }) => (
    <strong className="font-semibold text-text-primary">{children}</strong>
  ),
  em: ({ children }) => <em className="italic">{children}</em>,
  del: ({ children }) => (
    <del className="text-text-tertiary line-through">{children}</del>
  ),

  a: ({ href, children }) => {
    // `safeUrl` empties anything it will not vouch for. An anchor with no destination is
    // not a link, so the words it wrapped are shown as the text they always were.
    if (!href) return <span>{children}</span>;
    return (
      <a
        href={href}
        // The agent's links leave the product, and the conversation should survive being
        // followed. `noopener noreferrer` is what keeps the opened page from reaching back
        // through `window.opener` into a session it was never part of.
        target="_blank"
        rel="noopener noreferrer"
        className="font-medium text-primary-500 underline underline-offset-4 outline-none focus-visible:rounded-xs focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
      >
        {children}
      </a>
    );
  },

  ul: ({ children }) => (
    <ul className={cn(BLOCK, "list-disc space-y-1 pl-5")}>{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className={cn(BLOCK, "list-decimal space-y-1 pl-5")}>{children}</ol>
  ),
  li: ({ className, children }) => (
    <li
      className={cn(
        "marker:text-text-tertiary",
        // A GFM task list carries its own checkbox, and a bullet beside it reads as a
        // rendering fault. `mdast-util-to-hast` marks those rows for exactly this.
        className?.includes("task-list-item") && "-ml-5 list-none",
      )}
    >
      {children}
    </li>
  ),
  input: ({ checked }) => (
    <input
      type="checkbox"
      checked={Boolean(checked)}
      // A transcript is a record of what was said, not a form. The box reports state.
      disabled
      readOnly
      aria-hidden="true"
      className="mr-1.5 size-3.5 translate-y-0.5 rounded-xs border-card-border accent-primary-500"
    />
  ),

  // One weight for every level: six sizes of heading inside a chat bubble reads as a
  // document that wandered into the wrong container.
  h1: ({ children }) => <Heading>{children}</Heading>,
  h2: ({ children }) => <Heading>{children}</Heading>,
  h3: ({ children }) => <Heading>{children}</Heading>,
  h4: ({ children }) => <Heading>{children}</Heading>,
  h5: ({ children }) => <Heading>{children}</Heading>,
  h6: ({ children }) => <Heading>{children}</Heading>,

  blockquote: ({ children }) => (
    <blockquote
      className={cn(
        BLOCK,
        "border-l-2 border-card-border pl-3 text-text-secondary",
      )}
    >
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-3 border-card-border" />,

  // Inline code. Inside a fenced block the same element is reset by the `pre` below, which
  // owns the frame so the two do not nest one box inside another.
  code: ({ children }) => (
    <code className="rounded-md border border-card-border bg-background-gray-tertiary px-1 py-0.5 font-mono text-xs break-words">
      {children}
    </code>
  ),
  pre: ({ children }) => (
    <div
      className={cn(
        BLOCK,
        "scrollbar-thin overflow-x-auto rounded-lg border border-card-border bg-background-gray-tertiary",
      )}
    >
      {/* A code block scrolls rather than wraps, and never widens the panel. */}
      <pre className="w-max min-w-full px-3 py-2 font-mono text-xs leading-5 [&_code]:border-0 [&_code]:bg-transparent [&_code]:p-0">
        {children}
      </pre>
    </div>
  ),

  table: ({ children }) => (
    <div
      className={cn(
        BLOCK,
        "scrollbar-thin overflow-x-auto rounded-lg border border-card-border",
      )}
    >
      <table className="w-full border-collapse text-xs">{children}</table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-background-gray-secondary">{children}</thead>
  ),
  // The header row is separated by the cells' own rule, so the last body row can drop its
  // border without taking the header's with it.
  tr: ({ children }) => (
    <tr className="border-b border-card-border last:border-0">{children}</tr>
  ),
  th: ({ children }) => (
    <th className="border-b border-card-border px-2.5 py-1.5 text-left font-semibold whitespace-nowrap text-text-primary">
      {children}
    </th>
  ),
  td: ({ children }) => <td className="px-2.5 py-1.5 align-top">{children}</td>,
};

function Heading({ children }: { children?: ReactNode }) {
  return (
    <p className="mt-3 mb-1 text-sm leading-5 font-semibold text-text-primary first:mt-0">
      {children}
    </p>
  );
}

/** Module-level, so a new token does not rebuild react-markdown's processor every keystroke. */
const REMARK_PLUGINS = [remarkGfm];

export interface AgentMarkdownProps {
  /** Untrusted. Half-finished while a reply is still streaming, which is expected. */
  content: string;
}

/**
 * Memoised because a reply arriving token by token re-renders the whole transcript on every
 * delta, and every bubble above the one being written parses markdown it has already parsed.
 */
export const AgentMarkdown = memo(function AgentMarkdown({
  content,
}: AgentMarkdownProps) {
  return (
    <Markdown
      remarkPlugins={REMARK_PLUGINS}
      // No rehype plugins, and in particular no `rehype-raw`: see the note at the top.
      skipHtml
      allowedElements={ALLOWED_ELEMENTS}
      unwrapDisallowed
      urlTransform={safeUrl}
      components={COMPONENTS}
    >
      {content}
    </Markdown>
  );
});
