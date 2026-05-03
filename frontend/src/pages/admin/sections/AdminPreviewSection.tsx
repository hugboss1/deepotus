/**
 * AdminPreviewSection — "Preview" tab inside AdminBots.
 *
 * Sprint 21 — extracted from the AdminBots monolith. Owns:
 *   - all preview-related local state (content_type, platform, kol_post,
 *     v2 toggle, force_template_v2, news context, image toggles…)
 *   - the GET /content-types and GET /v2-templates fetches (auto-loaded)
 *   - the POST /generate-preview call
 *   - rendering of the Studio Input pane + Prophet Output pane
 *
 * Self-contained: only requires `api` + `headers` + a tiny `llmInfo`
 * tuple from the parent (used purely for the "Preview uses LLM: …"
 * subtitle so the admin sees which preset will run).
 *
 * The component does NOT mutate the bot config — it reads through props
 * for display purposes only and POSTs everything else against
 * /generate-preview which is a stateless dry-run endpoint.
 */

import { useCallback, useEffect, useState } from "react";
import axios from "axios";
// Sprint 22 — relaxed `AxiosRequestHeaders` to plain Record so the
// parent's `useMemo(() => ({ Authorization: ... }))` is assignable
// without an unsafe cast.
import { toast } from "sonner";
import {
  AlertTriangle,
  Download,
  Image as ImageIcon,
  Languages,
  Newspaper,
  RefreshCcw,
  Sparkles,
  Wand2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { logger } from "@/lib/logger";

const CONTENT_TYPE_ICONS: Record<string, string> = {
  prophecy: "🔮",
  market_commentary: "📰",
  vault_update: "🔐",
  kol_reply: "💬",
};

interface ContentTypeMeta {
  id: string;
  label_en: string;
  description_en: string;
}

interface V2TemplateMeta {
  id: string;
  weight: number;
  label_en: string;
}

interface PreviewImage {
  content_type: string;
  aspect_ratio: string;
  provider: string;
  model: string;
  mime_type: string;
  image_base64: string;
  size_bytes: number;
}

interface PreviewResponse {
  content_type: string;
  platform: string;
  char_budget: number;
  provider: string;
  model: string;
  content_fr: string;
  content_en: string;
  hashtags: string[];
  primary_emoji: string;
  image?: PreviewImage | null;
  image_error?: string | null;
  template_used?: string | null;
  template_label?: string | null;
}

interface Props {
  api: string;
  headers: Record<string, string>;
  /** Read-only display of the currently configured Prophet LLM. */
  llmInfo?: { provider?: string; model?: string };
}

export default function AdminPreviewSection({ api, headers, llmInfo }: Props) {
  // ---- Catalogues ----
  const [contentTypes, setContentTypes] = useState<ContentTypeMeta[]>([]);
  const [v2Templates, setV2Templates] = useState<V2TemplateMeta[]>([]);

  // ---- User input ----
  const [previewType, setPreviewType] = useState("prophecy");
  const [previewPlatform, setPreviewPlatform] = useState("x");
  const [kolPost, setKolPost] = useState("");
  const [previewKeywords, setPreviewKeywords] = useState("");
  const [useNewsContext, setUseNewsContext] = useState(false);

  // ---- Sprint 18 V2 controls ----
  const [useV2Preview, setUseV2Preview] = useState(false);
  const [forceTemplateV2, setForceTemplateV2] = useState("");

  // ---- Image controls ----
  const [includeImage, setIncludeImage] = useState(false);
  const [imageAspect, setImageAspect] = useState("16:9");
  const [imageProvider, setImageProvider] = useState<"gemini" | "openai">("gemini");

  // ---- Output ----
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [previewBusy, setPreviewBusy] = useState(false);

  // -------------------------------------------------------------------
  // Catalogue fetchers — invoked once on mount.
  // -------------------------------------------------------------------
  const loadContentTypes = useCallback(async () => {
    try {
      const { data } = await axios.get<ContentTypeMeta[]>(
        `${api}/api/admin/bots/content-types`,
        { headers },
      );
      setContentTypes(Array.isArray(data) ? data : []);
    } catch (err) {
      logger.error(err);
    }
  }, [api, headers]);

  const loadV2Templates = useCallback(async () => {
    try {
      const { data } = await axios.get<V2TemplateMeta[]>(
        `${api}/api/admin/bots/v2-templates`,
        { headers },
      );
      setV2Templates(Array.isArray(data) ? data : []);
    } catch (err) {
      logger.error(err);
    }
  }, [api, headers]);

  useEffect(() => {
    loadContentTypes();
    loadV2Templates();
  }, [loadContentTypes, loadV2Templates]);

  // -------------------------------------------------------------------
  // Generate preview
  // -------------------------------------------------------------------
  const generatePreview = useCallback(
    async (overrideProvider: "gemini" | "openai" | null = null) => {
      if (previewType === "kol_reply" && !kolPost.trim() && !useV2Preview) {
        toast.error("kol_post required for KOL reply");
        return;
      }
      const effectiveProvider = overrideProvider || imageProvider;
      setPreviewBusy(true);
      setPreview(null);

      try {
        // eslint-disable-next-line
        const body: Record<string, any> = {
          content_type: previewType,
          platform: previewPlatform,
          include_image: includeImage,
          image_provider: effectiveProvider,
          image_aspect_ratio: imageAspect,
          use_news_context: useNewsContext,
          use_v2: useV2Preview,
        };
        if (useV2Preview && forceTemplateV2) {
          body.force_template_v2 = forceTemplateV2;
        }
        if (previewType === "kol_reply" && !useV2Preview) {
          body.kol_post = kolPost.trim();
        }
        const cleanedKw = previewKeywords
          .split(",")
          .map((k) => k.trim())
          .filter(Boolean);
        if (cleanedKw.length) body.keywords = cleanedKw;

        const { data } = await axios.post<PreviewResponse>(
          `${api}/api/admin/bots/generate-preview`,
          body,
          {
            headers,
            timeout: effectiveProvider === "openai" ? 120_000 : 45_000,
          },
        );
        setPreview(data);
        if (data?.image?.provider === "gemini" || data?.image?.provider === "openai") {
          setImageProvider(data.image.provider);
        }

        const sparkParts: string[] = [];
        if (cleanedKw.length) sparkParts.push(`${cleanedKw.length} keyword(s)`);
        if (useNewsContext) sparkParts.push("latest news");
        const spark = sparkParts.length
          ? ` (spark: ${sparkParts.join(" + ")})`
          : "";
        const providerLabel =
          data?.image?.provider === "openai"
            ? "OpenAI gpt-image-1"
            : "Nano Banana";

        if (data.image_error) {
          toast.warning(`Image failed${spark}: ${data.image_error}`);
        } else if (data.image) {
          toast.success(
            `Prophet generated ${previewType} + ${providerLabel}${spark}`,
          );
        } else {
          toast.success(`Prophet generated a ${previewType} preview${spark}`);
        }
      } catch (err) {
        logger.error(err);
        // eslint-disable-next-line
        const msg = (err as any)?.response?.data?.detail || "Generation failed";
        toast.error(msg);
      } finally {
        setPreviewBusy(false);
      }
    },
    [
      api,
      headers,
      previewType,
      previewPlatform,
      kolPost,
      useNewsContext,
      useV2Preview,
      forceTemplateV2,
      previewKeywords,
      includeImage,
      imageAspect,
      imageProvider,
    ],
  );

  const downloadPreviewImage = useCallback(() => {
    if (!preview?.image?.image_base64) return;
    const { image_base64, mime_type, aspect_ratio, content_type, provider } =
      preview.image;
    const a = document.createElement("a");
    a.href = `data:${mime_type};base64,${image_base64}`;
    const ext = mime_type?.includes("jpeg") ? "jpg" : "png";
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    const providerSuffix = provider === "openai" ? "_openai" : "_gemini";
    a.download = `deepotus_${content_type}_${aspect_ratio.replace(":", "x")}${providerSuffix}_${ts}.${ext}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }, [preview]);

  const currentContentMeta = contentTypes.find((c) => c.id === previewType);

  return (
    <div
      className="grid grid-cols-1 lg:grid-cols-5 gap-5"
      data-testid="preview-section"
    >
      {/* ============================================================ */}
      {/*  LEFT COLUMN — Studio input                                  */}
      {/* ============================================================ */}
      <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Wand2 size={16} className="text-[#2DD4BF]" />
          <div className="font-display font-semibold">Studio input</div>
        </div>

        {/* Content type */}
        <div>
          <Label className="text-xs text-muted-foreground uppercase tracking-widest">
            Content type
          </Label>
          <Select value={previewType} onValueChange={setPreviewType}>
            <SelectTrigger className="mt-2" data-testid="preview-type-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {contentTypes.map((ct) => (
                <SelectItem key={ct.id} value={ct.id}>
                  {CONTENT_TYPE_ICONS[ct.id] || "•"} {ct.label_en}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {currentContentMeta && (
            <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
              {currentContentMeta.description_en}
            </p>
          )}
        </div>

        {/* Platform */}
        <div>
          <Label className="text-xs text-muted-foreground uppercase tracking-widest">
            Platform
          </Label>
          <Select value={previewPlatform} onValueChange={setPreviewPlatform}>
            <SelectTrigger
              className="mt-2"
              data-testid="preview-platform-select"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="x">X · 270 chars</SelectItem>
              <SelectItem value="telegram">Telegram · 800 chars</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* KOL body (only for kol_reply) */}
        {previewType === "kol_reply" && (
          <div>
            <Label className="text-xs text-muted-foreground uppercase tracking-widest">
              KOL tweet body
            </Label>
            <Textarea
              rows={4}
              placeholder="Paste the tweet the Prophet should reply to…"
              value={kolPost}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setKolPost(e.target.value)}
              className="mt-2 font-mono text-xs"
              data-testid="preview-kol-input"
            />
          </div>
        )}

        {/* Inspiration sources */}
        <div className="space-y-3 rounded-lg border border-border/60 bg-background/40 p-3">
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-[#2DD4BF]" />
            <Label className="font-medium text-sm">Prophet inspiration</Label>
          </div>
          <div>
            <Label className="text-xs text-muted-foreground uppercase tracking-widest">
              Keywords (comma separated)
            </Label>
            <Input
              value={previewKeywords}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setPreviewKeywords(e.target.value)}
              placeholder="e.g. powell, tariffs, OPEC squeeze"
              className="mt-2 font-mono text-xs"
              data-testid="preview-keywords-input"
            />
            <p className="mt-1 text-[10.5px] text-muted-foreground leading-relaxed">
              The Prophet weaves at least one of these into its cynical
              commentary — without quoting them verbatim.
            </p>
          </div>
          <div className="flex items-center justify-between gap-2 pt-1">
            <div className="flex items-center gap-2">
              <Newspaper size={14} className="text-[#F59E0B]" />
              <Label className="text-sm">Use latest news headlines</Label>
            </div>
            <Switch
              checked={useNewsContext}
              onCheckedChange={setUseNewsContext}
              data-testid="preview-news-toggle"
            />
          </div>
          {useNewsContext && (
            <p className="text-[10.5px] text-muted-foreground leading-relaxed">
              Top 5 geopolitics/macro headlines from the RSS aggregator are
              injected as inspiration. Configure feeds + keywords in the
              Config tab.
            </p>
          )}
        </div>

        <Separator />

        {/* V2 controls */}
        <div className="space-y-3 rounded-lg border border-border/60 bg-background/40 p-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Sparkles size={14} className="text-[#F59E0B]" />
              <Label className="font-medium text-sm">
                Use Prompt V2 (5 weighted templates)
              </Label>
            </div>
            <Switch
              checked={useV2Preview}
              onCheckedChange={setUseV2Preview}
              data-testid="preview-v2-toggle"
            />
          </div>
          {useV2Preview && (
            <>
              <p className="text-[10.5px] text-muted-foreground leading-relaxed">
                Routes through{" "}
                <span className="font-mono">generate_post_v2()</span>. The
                content type / KOL post above are ignored. Pick a specific
                template below to override the weighted random pick.
              </p>
              <div>
                <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                  Force template (optional)
                </Label>
                <Select
                  value={forceTemplateV2 || "__random__"}
                  onValueChange={(v: string) =>
                    setForceTemplateV2(v === "__random__" ? "" : v)
                  }
                >
                  <SelectTrigger
                    className="mt-2"
                    data-testid="preview-v2-template-select"
                  >
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__random__">
                      ⚖ Weighted random (4·3·1·1·1)
                    </SelectItem>
                    {v2Templates.map((tpl) => (
                      <SelectItem key={tpl.id} value={tpl.id}>
                        {tpl.id} · weight {tpl.weight} — {tpl.label_en}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </>
          )}
        </div>

        <Separator />

        {/* Image controls */}
        <div className="space-y-3 rounded-lg border border-border/60 bg-background/40 p-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <ImageIcon size={14} className="text-[#F59E0B]" />
              <Label className="font-medium text-sm">
                Nano Banana illustration
              </Label>
            </div>
            <Switch
              checked={includeImage}
              onCheckedChange={setIncludeImage}
              data-testid="preview-image-toggle"
            />
          </div>
          {includeImage && (
            <div>
              <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                Aspect ratio
              </Label>
              <Select value={imageAspect} onValueChange={setImageAspect}>
                <SelectTrigger
                  className="mt-2"
                  data-testid="preview-image-ratio"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="16:9">16:9 · X landscape</SelectItem>
                  <SelectItem value="3:4">3:4 · X portrait</SelectItem>
                  <SelectItem value="1:1">1:1 · Square</SelectItem>
                </SelectContent>
              </Select>
              <p className="mt-2 text-[11px] text-muted-foreground leading-relaxed">
                <strong className="text-foreground/80">
                  Default provider:
                </strong>{" "}
                Gemini Nano Banana — fast (~8–20s), free via{" "}
                <code className="font-mono text-[10px]">
                  EMERGENT_LLM_KEY
                </code>
                . Use the{" "}
                <strong className="text-[#F59E0B]">
                  Try OpenAI variant
                </strong>{" "}
                button below the preview to regenerate with{" "}
                <code className="font-mono text-[10px]">gpt-image-1</code>{" "}
                (~60s, better text rendering, ~$0.03/img).
              </p>
            </div>
          )}
        </div>

        <Button
          onClick={() => generatePreview("gemini")}
          disabled={previewBusy}
          className="w-full rounded-[var(--btn-radius)] btn-press font-semibold"
          data-testid="preview-generate-button"
        >
          {previewBusy && imageProvider === "gemini" ? (
            <>
              <RefreshCcw size={14} className="mr-2 animate-spin" />
              {includeImage
                ? "Generating text + Nano Banana…"
                : "Generating…"}
            </>
          ) : (
            <>
              <Sparkles size={14} className="mr-2" />
              {includeImage
                ? "Generate text + Nano Banana"
                : "Generate preview"}
            </>
          )}
        </Button>

        <div className="font-mono text-[10px] text-muted-foreground">
          Preview uses LLM:{" "}
          <span className="text-foreground/80">
            {llmInfo?.provider}/{llmInfo?.model}
          </span>
        </div>
      </div>

      {/* ============================================================ */}
      {/*  RIGHT COLUMN — Prophet output                               */}
      {/* ============================================================ */}
      <div className="lg:col-span-3 rounded-xl border border-border bg-card p-5 space-y-4 min-h-[320px]">
        <div className="flex items-center gap-2">
          <Languages size={16} className="text-muted-foreground" />
          <div className="font-display font-semibold">Prophet output</div>
          {preview && (
            <Badge
              variant="outline"
              className="ml-auto font-mono text-[10px] uppercase tracking-widest"
              data-testid="preview-output-badge"
            >
              {preview.char_budget} chars · {preview.platform}
            </Badge>
          )}
        </div>

        {!preview && !previewBusy && (
          <div className="flex flex-col items-center justify-center py-12 text-center gap-2 text-muted-foreground">
            <Wand2 size={24} />
            <div className="font-mono text-xs uppercase tracking-widest">
              Awaiting generation
            </div>
            <div className="text-xs max-w-xs">
              Pick a content type + platform on the left, then hit
              &quot;Generate preview&quot;. Nothing is posted — pure dry-run.
            </div>
          </div>
        )}

        {preview && (
          <div className="space-y-4">
            {preview.template_used && (
              <div
                className="rounded-md border border-[#F59E0B]/30 bg-[#F59E0B]/5 px-3 py-2 flex items-center gap-2"
                data-testid="preview-v2-template-badge"
              >
                <Sparkles size={13} className="text-[#F59E0B]" />
                <span className="font-mono text-[10px] uppercase tracking-widest text-[#F59E0B]">
                  V2 Template
                </span>
                <span className="font-mono text-[11px]">
                  {preview.template_used}
                </span>
                <span className="text-xs text-muted-foreground ml-auto">
                  {preview.template_label}
                </span>
              </div>
            )}
            <div className="rounded-lg border border-border/80 bg-background/40 p-4">
              <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
                FR · {preview.content_fr.length}/{preview.char_budget}
              </div>
              <p
                className="text-sm leading-relaxed whitespace-pre-wrap"
                data-testid="preview-output-fr"
              >
                {preview.content_fr}
              </p>
            </div>
            <div className="rounded-lg border border-border/80 bg-background/40 p-4">
              <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
                EN · {preview.content_en.length}/{preview.char_budget}
              </div>
              <p
                className="text-sm leading-relaxed whitespace-pre-wrap"
                data-testid="preview-output-en"
              >
                {preview.content_en}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {preview.primary_emoji && (
                <span
                  className="text-2xl leading-none"
                  aria-label="primary emoji"
                >
                  {preview.primary_emoji}
                </span>
              )}
              {(preview.hashtags || []).map((h) => (
                <Badge
                  key={h}
                  variant="secondary"
                  className="font-mono text-[10px] uppercase tracking-widest"
                >
                  #{h}
                </Badge>
              ))}
            </div>

            {/* Illustration block */}
            {preview.image && (
              <div
                className="rounded-lg border border-border/80 bg-background/40 p-4 space-y-3"
                data-testid="preview-output-image-block"
              >
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <ImageIcon
                      size={14}
                      className={
                        preview.image.provider === "openai"
                          ? "text-[#10B981]"
                          : "text-[#F59E0B]"
                      }
                    />
                    <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                      Illustration · {preview.image.aspect_ratio} ·{" "}
                      {Math.round((preview.image.size_bytes || 0) / 1024)} KB
                    </div>
                    <Badge
                      variant="outline"
                      className={
                        preview.image.provider === "openai"
                          ? "text-[10px] border-[#10B981]/50 text-[#10B981]"
                          : "text-[10px] border-[#F59E0B]/50 text-[#F59E0B]"
                      }
                      data-testid="preview-output-image-provider"
                    >
                      {preview.image.provider === "openai"
                        ? "OpenAI gpt-image-1"
                        : "Nano Banana"}
                    </Badge>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={downloadPreviewImage}
                    className="h-7 rounded-[var(--btn-radius)]"
                    data-testid="preview-output-image-download"
                  >
                    <Download size={12} className="mr-1" /> Download
                  </Button>
                </div>
                <div className="rounded-md overflow-hidden border border-border/60 bg-black">
                  <img
                    src={`data:${preview.image.mime_type};base64,${preview.image.image_base64}`}
                    alt="Prophet Studio illustration"
                    className="w-full h-auto block"
                    data-testid="preview-output-image"
                  />
                </div>
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="font-mono text-[10px] text-muted-foreground">
                    via {preview.image.provider}/{preview.image.model}
                  </div>
                  {preview.image.provider === "gemini" && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => generatePreview("openai")}
                      disabled={previewBusy}
                      className="h-7 rounded-[var(--btn-radius)] border-[#10B981]/50 text-[#10B981] hover:bg-[#10B981]/10"
                      data-testid="preview-try-openai-variant"
                    >
                      {previewBusy ? (
                        <RefreshCcw
                          size={11}
                          className="mr-1 animate-spin"
                        />
                      ) : (
                        <Sparkles size={11} className="mr-1" />
                      )}
                      Try OpenAI variant (~60s)
                    </Button>
                  )}
                  {preview.image.provider === "openai" && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => generatePreview("gemini")}
                      disabled={previewBusy}
                      className="h-7 rounded-[var(--btn-radius)] border-[#F59E0B]/50 text-[#F59E0B] hover:bg-[#F59E0B]/10"
                      data-testid="preview-try-gemini-variant"
                    >
                      {previewBusy ? (
                        <RefreshCcw
                          size={11}
                          className="mr-1 animate-spin"
                        />
                      ) : (
                        <Sparkles size={11} className="mr-1" />
                      )}
                      Try Gemini variant
                    </Button>
                  )}
                </div>
              </div>
            )}

            {preview.image_error && !preview.image && (
              <div
                className="rounded-md border border-[#E11D48]/40 bg-[#E11D48]/5 p-3 flex items-start gap-2"
                data-testid="preview-output-image-error"
              >
                <AlertTriangle
                  size={14}
                  className="text-[#E11D48] shrink-0 mt-0.5"
                />
                <div className="text-xs">
                  <div className="font-mono text-[10px] uppercase tracking-widest text-[#E11D48]">
                    Image generation failed
                  </div>
                  <div className="text-foreground/80 mt-1">
                    {preview.image_error}
                  </div>
                </div>
              </div>
            )}

            <div className="font-mono text-[10px] text-muted-foreground">
              text via {preview.provider}/{preview.model}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
