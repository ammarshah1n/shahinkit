/**
 * image-guard — stops the whole session dying on one bad image.
 *
 * Symptom this fixes:
 *   "System error, codec error, the image data you provided does not represent a
 *    valid image. Please check your input and try again with one of the supported
 *    image formats [image/jpeg, image/png, image/gif, image/webp]"
 *   stop_reason=error, on every subsequent turn, because the bad image part stays
 *   in the conversation history and is re-sent forever.
 *
 * Causes seen in the wild:
 *   - a screenshot/paste whose declared media type does not match the actual bytes
 *     (PNG bytes labelled image/jpeg, HEIC/PDF/SVG/BMP labelled image/png)
 *   - a truncated or zero-byte file read as an image attachment
 *   - a data: URL with whitespace/newlines or a stray "data:image/png;base64," prefix
 *     duplicated inside the payload
 *
 * What it does, in before_provider_request (last hook before the wire):
 *   1. sniffs the real format from magic bytes
 *   2. if the format is supported but mislabelled -> rewrites the media type (repair)
 *   3. if the bytes are not a supported image at all -> replaces the image part with
 *      a short text note (drop), so the turn succeeds instead of erroring
 *
 * Handles both payload shapes: Anthropic content blocks
 * ({type:"image", source:{type:"base64", media_type, data}}) and OpenAI/Codex
 * ({type:"input_image", image_url:"data:...;base64,..."}).
 */

const SUPPORTED = ["image/jpeg", "image/png", "image/gif", "image/webp"] as const;

/** Sniff a supported image type from the first bytes. Returns null if unsupported. */
function sniff(bytes: Uint8Array): string | null {
  const b = bytes;
  if (b.length < 12) return null;
  if (b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) return "image/jpeg";
  if (
    b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47 &&
    b[4] === 0x0d && b[5] === 0x0a && b[6] === 0x1a && b[7] === 0x0a
  ) return "image/png";
  if (b[0] === 0x47 && b[1] === 0x49 && b[2] === 0x46 && b[3] === 0x38) return "image/gif";
  if (
    b[0] === 0x52 && b[1] === 0x49 && b[2] === 0x46 && b[3] === 0x46 &&
    b[8] === 0x57 && b[9] === 0x45 && b[10] === 0x42 && b[11] === 0x50
  ) return "image/webp";
  return null;
}

function decodeHead(data: string): Uint8Array | null {
  try {
    // 64 base64 chars is plenty for every magic number above, and keeps this cheap
    // on multi-megabyte screenshots.
    const head = data.replace(/\s+/g, "").slice(0, 64);
    return new Uint8Array(Buffer.from(head, "base64"));
  } catch {
    return null;
  }
}

type Check =
  | { ok: true; type: string }
  | { ok: false; reason: string };

function check(data: string | undefined | null): Check {
  const clean = (data ?? "").replace(/\s+/g, "");
  if (!clean) return { ok: false, reason: "empty image data" };
  const head = decodeHead(clean);
  if (!head || head.length === 0) return { ok: false, reason: "image data is not valid base64" };
  const type = sniff(head);
  if (!type) return { ok: false, reason: "bytes are not jpeg/png/gif/webp" };
  return { ok: true, type };
}

function note(reason: string): { type: "text"; text: string } {
  return {
    type: "text",
    text: `[image-guard: dropped an unsupported image attachment — ${reason}. Supported: ${SUPPORTED.join(", ")}.]`,
  };
}

/** Rewrites one content part. Returns the part (possibly repaired/replaced). */
function fixPart(part: any, stats: { repaired: number; dropped: number }): any {
  if (!part || typeof part !== "object") return part;

  // Anthropic: { type:"image", source:{ type:"base64", media_type, data } }
  if (part.type === "image" && part.source?.type === "base64") {
    const r = check(part.source.data);
    if (!r.ok) {
      stats.dropped++;
      return note(r.reason);
    }
    if (part.source.media_type !== r.type) {
      stats.repaired++;
      return { ...part, source: { ...part.source, media_type: r.type, data: String(part.source.data).replace(/\s+/g, "") } };
    }
    return part;
  }

  // Anthropic url-source or OpenAI image_url — only data: URLs are checkable.
  const url: unknown =
    part.type === "input_image" || part.type === "image_url" || part.type === "image"
      ? (typeof part.image_url === "string" ? part.image_url : part.image_url?.url ?? part.source?.url)
      : undefined;

  if (typeof url === "string" && url.startsWith("data:")) {
    const m = /^data:([^;,]*)?;base64,([\s\S]*)$/.exec(url);
    if (!m) {
      stats.dropped++;
      return note("data URL is not base64-encoded");
    }
    const r = check(m[2]);
    if (!r.ok) {
      stats.dropped++;
      return note(r.reason);
    }
    const rebuilt = `data:${r.type};base64,${m[2].replace(/\s+/g, "")}`;
    if (rebuilt !== url) {
      stats.repaired++;
      if (typeof part.image_url === "string") return { ...part, image_url: rebuilt };
      if (part.image_url?.url) return { ...part, image_url: { ...part.image_url, url: rebuilt } };
      if (part.source?.url) return { ...part, source: { ...part.source, url: rebuilt } };
    }
    return part;
  }

  return part;
}

/** Deep-walks any provider payload shape and fixes every image part found. */
function walk(node: any, stats: { repaired: number; dropped: number }): any {
  if (Array.isArray(node)) return node.map((n) => walk(fixPart(n, stats), stats));
  if (node && typeof node === "object") {
    const out: any = Array.isArray(node) ? [] : { ...node };
    for (const k of Object.keys(out)) {
      const v = out[k];
      if (v && typeof v === "object") out[k] = walk(v, stats);
    }
    return out;
  }
  return node;
}

export default function imageGuard(pi: any) {
  pi.on("before_provider_request", (event: any, ctx: any) => {
    const stats = { repaired: 0, dropped: 0 };
    let payload: any;
    try {
      payload = walk(event.payload, stats);
    } catch {
      return undefined; // never break a request because the guard failed
    }
    if (stats.repaired === 0 && stats.dropped === 0) return undefined;
    try {
      ctx?.ui?.setStatus?.(
        `image-guard: ${stats.repaired} repaired, ${stats.dropped} dropped`,
      );
    } catch { /* status is cosmetic */ }
    return payload;
  });
}
