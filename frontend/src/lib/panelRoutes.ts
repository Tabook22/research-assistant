/** Workspace sections that can open as a dedicated full page / new tab. */

export const PANEL_TABS = [
  "profile",
  "questions",
  "structure",
  "suggestions",
  "library",
  "synthesis",
  "benchmark",
  "alignment",
  "literature",
  "documents",
  "export",
] as const;

export type PanelTab = (typeof PANEL_TABS)[number];

/** Extra full-page targets beyond the right-side tabs. */
export const STANDALONE_SECTIONS = ["chat", "stages", ...PANEL_TABS] as const;
export type StandaloneSection = (typeof STANDALONE_SECTIONS)[number];

export function isPanelTab(value: string | undefined | null): value is PanelTab {
  return !!value && (PANEL_TABS as readonly string[]).includes(value);
}

export function isStandaloneSection(
  value: string | undefined | null
): value is StandaloneSection {
  return !!value && (STANDALONE_SECTIONS as readonly string[]).includes(value);
}

/** Canonical URL for a workspace section (library keeps its existing path). */
export function panelUrl(projectId: number, section: StandaloneSection | string): string {
  if (section === "library") return `/projects/${projectId}/library`;
  return `/projects/${projectId}/panel/${section}`;
}
