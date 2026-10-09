// Normalize provider-bound images to supported MIME types, dimensions, and payload size.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

export const MAX_BASE64_BYTES = 10 * 1024 * 1024;
export const MAX_LONG_EDGE = 1568;
const ACCEPTED = new Set(["image/jpeg", "image/png", "image/gif", "image/webp"]);
const JPEG_SOF = new Set([0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf]);
export type ImageBlock = { type: "image"; data: string; mimeType: string };
export type Dimensions = { width: number; height: number };
export type NormalizationResult = { block: ImageBlock; changed: boolean; reason?: "mime" | "normalized" };
export type NormalizeOptions = { binaries?: string[] };
const ascii = (b: Uint8Array, i: number, n: number) => Buffer.from(b.subarray(i, i + n)).toString("ascii");
const u16 = (b: Uint8Array, i: number) => i + 2 <= b.length ? b[i] * 256 + b[i + 1] : undefined;
const u32 = (b: Uint8Array, i: number) => i + 4 <= b.length ? (b[i] * 0x1000000 + (b[i + 1] << 16) + (b[i + 2] << 8) + b[i + 3]) >>> 0 : undefined;

export function sniffMimeType(b: Uint8Array): string | undefined {
  if (b.length >= 3 && b[0] === 255 && b[1] === 216 && b[2] === 255) return "image/jpeg";
  if (b.length >= 8 && b[0] === 137 && ascii(b, 1, 3) === "PNG" && b[4] === 13 && b[5] === 10 && b[6] === 26 && b[7] === 10) return "image/png";
  if (b.length >= 6 && ["GIF87a", "GIF89a"].includes(ascii(b, 0, 6))) return "image/gif";
  if (b.length >= 12 && ascii(b, 0, 4) === "RIFF" && ascii(b, 8, 4) === "WEBP") return "image/webp";
  if (b.length >= 12 && ascii(b, 4, 4) === "ftyp") {
    const brands = Array.from({ length: Math.floor((Math.min(b.length, 64) - 8) / 4) }, (_, n) => ascii(b, 8 + n * 4, 4));
    if (brands.some((x) => ["heic", "heix", "hevc", "hevx", "mif1", "msf1"].includes(x))) return "image/heic";
    if (brands.some((x) => ["avif", "avis"].includes(x))) return "image/avif";
  }
  return undefined;
}
export function dimensionsFromBytes(b: Uint8Array, mime = sniffMimeType(b)): Dimensions | undefined {
  if (mime === "image/png") { const width = u32(b, 16), height = u32(b, 20); return width && height ? { width, height } : undefined; }
  if (mime === "image/gif" && b.length >= 10) { const width = b[6] | b[7] << 8, height = b[8] | b[9] << 8; return width && height ? { width, height } : undefined; }
  if (mime === "image/jpeg") {
    let i = 2;
    while (i + 9 <= b.length) {
      while (b[i] === 255) i++;
      const marker = b[i++];
      if (marker === undefined || marker === 217 || marker === 218) break;
      if (marker === 1 || (marker >= 208 && marker <= 215)) continue;
      const length = u16(b, i); if (!length || length < 2 || i + length > b.length) break;
      if (JPEG_SOF.has(marker)) { const height = u16(b, i + 3), width = u16(b, i + 5); return width && height ? { width, height } : undefined; }
      i += length;
    }
  }
  if ((mime === "image/heic" || mime === "image/avif") && b.length >= 20) {
    for (let i = 4; i + 16 <= b.length; i++) if (ascii(b, i, 4) === "ispe") { const width = u32(b, i + 8), height = u32(b, i + 12); if (width && height) return { width, height }; }
  }
  if (mime === "image/webp" && b.length >= 30) {
    const kind = ascii(b, 12, 4);
    if (kind === "VP8X") return { width: 1 + b[24] + (b[25] << 8) + (b[26] << 16), height: 1 + b[27] + (b[28] << 8) + (b[29] << 16) };
    if (kind === "VP8 " && b[23] === 157 && b[24] === 1 && b[25] === 42) return { width: (b[26] | b[27] << 8) & 16383, height: (b[28] | b[29] << 8) & 16383 };
    if (kind === "VP8L" && b[20] === 47) return { width: 1 + b[21] + ((b[22] & 63) << 8), height: 1 + ((b[22] >> 6) | (b[23] << 2) | ((b[24] & 15) << 10)) };
  }
  return undefined;
}
function cleanBase64(value: unknown): string | undefined {
  if (typeof value !== "string") return;
  const clean = value.replace(/\s+/g, "");
  return clean && clean.length % 4 === 0 && /^[A-Za-z0-9+/]*={0,2}$/.test(clean) ? clean : undefined;
}
function defaultBinaries() { return process.platform === "darwin" ? ["/usr/bin/sips", "magick", "convert"] : ["magick", "convert"]; }
async function run(command: string, args: string[], capture = false): Promise<{ ok: boolean; stdout: string }> {
  return new Promise((resolve) => {
    let stdout = "", done = false;
    const finish = (ok: boolean) => { if (!done) { done = true; clearTimeout(timer); resolve({ ok, stdout }); } };
    let child: ReturnType<typeof spawn>;
    try { child = spawn(command, args, { stdio: capture ? ["ignore", "pipe", "ignore"] : "ignore" }); } catch { resolve({ ok: false, stdout }); return; }
    const timer = setTimeout(() => child.kill("SIGKILL"), 20_000);
    child.stdout?.on("data", (chunk: Buffer) => { if (stdout.length < 8192) stdout += chunk.toString("utf8"); });
    child.on("error", () => finish(false)); child.on("exit", (code) => finish(code === 0));
  });
}
function parseDimensions(output: string): Dimensions | undefined {
  const match = output.match(/(\d+)\D+(\d+)(?!.*\d)/);
  if (!match) return;
  const width = Number(match[1]), height = Number(match[2]);
  return Number.isSafeInteger(width) && Number.isSafeInteger(height) && width > 0 && height > 0 ? { width, height } : undefined;
}
async function inspectDimensions(file: string, binaries: string[]): Promise<Dimensions | undefined> {
  for (const bin of binaries) {
    const r = bin === "/usr/bin/sips" ? await run(bin, ["-g", "pixelWidth", "-g", "pixelHeight", file], true)
      : bin === "magick" ? await run(bin, ["identify", "-format", "%w %h", file], true)
      : await run(bin, [file, "-format", "%w %h", "info:"], true);
    if (r.ok) { const d = parseDimensions(r.stdout); if (d) return d; }
  }
}
async function render(input: string, output: string, edge: number, binaries: string[], quality?: number): Promise<boolean> {
  for (const bin of binaries) {
    const args = bin === "/usr/bin/sips"
      ? quality === undefined ? ["-Z", String(edge), input, "--out", output] : ["-s", "format", "jpeg", "-s", "formatOptions", String(quality), "-Z", String(edge), input, "--out", output]
      : [input, "-auto-orient", "-resize", `${edge}x${edge}>`, ...(quality === undefined ? [] : ["-strip", "-quality", String(quality)]), output];
    if (await run(bin, bin === "magick" ? ["convert", ...args] : args)) return true;
  }
  return false;
}
export async function normalizeImageBlock(block: ImageBlock, options: NormalizeOptions = {}): Promise<NormalizationResult> {
  try {
    const clean = cleanBase64(block.data); if (!clean) return { block, changed: false };
    const bytes = new Uint8Array(Buffer.from(clean, "base64")); if (!bytes.length) return { block, changed: false };
    const actual = sniffMimeType(bytes), hd = dimensionsFromBytes(bytes, actual);
    const within = hd && Math.max(hd.width, hd.height) <= MAX_LONG_EDGE;
    if (actual && ACCEPTED.has(actual) && within && Buffer.byteLength(clean, "ascii") <= MAX_BASE64_BYTES)
      return block.mimeType === actual && block.data === clean ? { block, changed: false } : { block: { ...block, data: clean, mimeType: actual }, changed: true, reason: "mime" };
    const bins = options.binaries ?? defaultBinaries(); if (!bins.length) return { block, changed: false };
    const dir = await mkdtemp(join(tmpdir(), "pi-image-cap-"));
    try {
      const input = join(dir, "input"); await writeFile(input, bytes);
      const dimensions = hd ?? await inspectDimensions(input, bins); if (!dimensions) return { block, changed: false };
      const ext = actual === "image/jpeg" ? "jpg" : actual?.split("/")[1];
      let edge = Math.min(MAX_LONG_EDGE, Math.max(dimensions.width, dimensions.height));
      while (edge >= 1) {
        if (actual && ACCEPTED.has(actual) && ext && await render(input, join(dir, `out-${edge}.${ext}`), edge, bins)) {
          const candidate = new Uint8Array(await readFile(join(dir, `out-${edge}.${ext}`))), mime = sniffMimeType(candidate), d = dimensionsFromBytes(candidate, mime), data = Buffer.from(candidate).toString("base64");
          if (mime === actual && d && Math.max(d.width, d.height) <= MAX_LONG_EDGE && data.length <= MAX_BASE64_BYTES) return { block: { ...block, data, mimeType: mime }, changed: true, reason: "normalized" };
        }
        for (const quality of [85, 70, 55, 40, 25]) {
          const output = join(dir, `out-${edge}-${quality}.jpg`);
          if (!await render(input, output, edge, bins, quality)) continue;
          const candidate = new Uint8Array(await readFile(output)), mime = sniffMimeType(candidate), d = dimensionsFromBytes(candidate, mime), data = Buffer.from(candidate).toString("base64");
          if (mime === "image/jpeg" && d && Math.max(d.width, d.height) <= MAX_LONG_EDGE && data.length <= MAX_BASE64_BYTES) return { block: { ...block, data, mimeType: mime }, changed: true, reason: "normalized" };
        }
        if (edge === 1) break; edge = Math.max(1, Math.floor(edge * 0.75));
      }
      return { block, changed: false };
    } finally { await rm(dir, { recursive: true, force: true }).catch(() => undefined); }
  } catch { return { block, changed: false }; }
}
export async function normalizeImageBlocks<T>(content: T[], options: NormalizeOptions = {}): Promise<{ content: T[]; changed: boolean }> {
  let changed = false; const normalized: T[] = [];
  for (const part of content) {
    if (!part || typeof part !== "object" || (part as any).type !== "image") { normalized.push(part); continue; }
    const result = await normalizeImageBlock(part as ImageBlock, options); normalized.push(result.block as T); changed ||= result.changed;
  }
  return changed ? { content: normalized, changed: true } : { content, changed: false };
}
export function inspectImageBlock(block: ImageBlock): { mimeType?: string; dimensions?: Dimensions; bytes: number; base64Bytes: number } {
  const clean = cleanBase64(block.data); if (!clean) return { bytes: 0, base64Bytes: 0 };
  const bytes = new Uint8Array(Buffer.from(clean, "base64")), mimeType = sniffMimeType(bytes);
  return { mimeType, dimensions: dimensionsFromBytes(bytes, mimeType), bytes: bytes.length, base64Bytes: Buffer.byteLength(clean, "ascii") };
}
export function imageViolations(block: ImageBlock): string[] {
  const image = inspectImageBlock(block), out: string[] = [];
  if (!image.mimeType || !ACCEPTED.has(image.mimeType)) out.push("media type");
  if (block.mimeType !== image.mimeType) out.push("mimeType mismatch");
  if (!image.dimensions || Math.max(image.dimensions.width, image.dimensions.height) > MAX_LONG_EDGE) out.push("dimensions");
  if (image.base64Bytes > MAX_BASE64_BYTES) out.push("base64 bytes");
  return out;
}
export default function imageCap(pi: ExtensionAPI) {
  pi.on("input", async (event: any) => {
    if (!event.images?.length) return { action: "continue" };
    const result = await normalizeImageBlocks(event.images);
    return result.changed ? { action: "transform", text: event.text, images: result.content } : { action: "continue" };
  });
  pi.on("message_end", async (event: any) => {
    const content = event.message?.content;
    if (!Array.isArray(content) || !content.some((p: any) => p?.type === "image")) return;
    const result = await normalizeImageBlocks(content);
    return result.changed ? { message: { ...event.message, content: result.content } } : undefined;
  });
  pi.on("context", async (event: any) => {
    let changed = false; const messages = [];
    for (const message of event.messages) {
      if (!Array.isArray((message as any).content)) { messages.push(message); continue; }
      const result = await normalizeImageBlocks((message as any).content);
      messages.push(result.changed ? { ...message, content: result.content } : message); changed ||= result.changed;
    }
    return changed ? { messages } : undefined;
  });
}
