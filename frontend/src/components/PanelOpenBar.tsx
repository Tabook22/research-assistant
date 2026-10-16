import { Link } from "react-router-dom";

type Props = {
  fullPageHref: string;
  openFullPageLabel: string;
  openNewTabLabel: string;
  hint?: string;
  /** Compact bar without the long hint (e.g. in panel headers). */
  compact?: boolean;
};

/** Shared control: open the current workspace section on its own page or in a new tab. */
export default function PanelOpenBar({
  fullPageHref,
  openFullPageLabel,
  openNewTabLabel,
  hint,
  compact = true,
}: Props) {
  return (
    <div className={`library-open-bar panel-open-bar${compact ? " panel-open-bar--compact" : ""}`}>
      {!compact && hint ? (
        <p className="muted" style={{ margin: 0, flex: 1, fontSize: "0.85rem" }}>
          {hint}
        </p>
      ) : (
        <span style={{ flex: 1 }} />
      )}
      <div className="library-open-actions">
        <Link className="btn btn-ghost" to={fullPageHref}>
          {openFullPageLabel}
        </Link>
        <a className="btn" href={fullPageHref} target="_blank" rel="noreferrer">
          {openNewTabLabel}
        </a>
      </div>
    </div>
  );
}
