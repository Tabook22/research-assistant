/**
 * Pull real project data into each research stage for graphical boards.
 */

import type {
  Objective,
  Profile,
  Project,
  Question,
  Reference,
  SourceDocumentSummary,
} from "../types";
import { getStageGuide } from "../i18n/stageGuides";

export type StageDataItem = {
  label: string;
  value: string;
  filled: boolean;
};

export type StageSnapshot = {
  stageKey: string;
  status: string;
  isCurrent: boolean;
  isComplete: boolean;
  completedAt?: string | null;
  guideInputs: string;
  guideProcessing: string;
  guideOutputs: string;
  nextStageKey: string | null;
  /** Real fields feeding this stage */
  inputData: StageDataItem[];
  /** Real fields produced / expected as outputs */
  outputData: StageDataItem[];
  readinessPercent: number;
};

function clip(s: string | null | undefined, n = 180): string {
  if (!s || !String(s).trim()) return "";
  const t = String(s).trim().replace(/\s+/g, " ");
  return t.length > n ? t.slice(0, n - 1) + "…" : t;
}

function item(label: string, value: string | null | undefined): StageDataItem {
  const v = clip(value);
  return { label, value: v || "—", filled: Boolean(v) };
}

export type StageProjectContext = {
  project: Project;
  questions: Question[];
  objectives: Objective[];
  references: Reference[];
  libraryDocs: SourceDocumentSummary[];
  documentCount?: number;
  lang: "en" | "ar";
};

function profile(p: Project): Profile | undefined {
  return p.profile || undefined;
}

/** Build real-data snapshot for one stage key. */
export function buildStageSnapshot(
  stageKey: string,
  status: string,
  ctx: StageProjectContext
): StageSnapshot {
  const { project, questions, objectives, references, libraryDocs, lang } = ctx;
  const pr = profile(project);
  const guide = getStageGuide(lang, stageKey);
  const isCurrent = project.current_stage === stageKey;
  const isComplete = status === "completed";
  const prog = project.stage_progress?.find((s) => s.stage_key === stageKey);

  let inputData: StageDataItem[] = [];
  let outputData: StageDataItem[] = [];

  const title = item(
    lang === "ar" ? "عنوان المشروع" : "Project title",
    project.working_title
  );
  const field = item(
    lang === "ar" ? "المجال" : "Field",
    project.research_field
  );
  const pop = item(
    lang === "ar" ? "المجتمع" : "Population",
    project.population_summary
  );
  const docType = item(
    lang === "ar" ? "نوع الوثيقة" : "Document type",
    project.document_type
  );

  switch (stageKey) {
    case "idea":
      inputData = [
        title,
        field,
        item(lang === "ar" ? "السياق" : "Context", project.study_context),
      ];
      outputData = [
        item(lang === "ar" ? "الفكرة المنقّحة" : "Refined idea", pr?.refined_idea),
        item(lang === "ar" ? "المفاهيم الرئيسة" : "Key concepts", pr?.key_concepts),
        item(lang === "ar" ? "نطاق مقترح" : "Proposed scope", pr?.proposed_scope),
      ];
      break;
    case "literature_search":
      inputData = [
        item(lang === "ar" ? "مصطلحات البحث" : "Search terms", pr?.initial_search_terms),
        item(lang === "ar" ? "المفاهيم" : "Concepts", pr?.key_concepts),
        field,
      ];
      outputData = [
        item(
          lang === "ar" ? "مراجع محفوظة" : "Saved references",
          String(references.length)
        ),
        item(
          lang === "ar" ? "أوراق المكتبة" : "Library papers",
          String(libraryDocs.length)
        ),
      ];
      break;
    case "literature_synthesis":
      inputData = [
        item(
          lang === "ar" ? "عدد المراجع" : "Reference count",
          String(references.length)
        ),
        item(
          lang === "ar" ? "أوراق للدراسة" : "Study papers",
          String(libraryDocs.length)
        ),
        item(lang === "ar" ? "أدلة موجودة" : "Existing evidence", pr?.existing_evidence),
      ];
      outputData = [
        item(lang === "ar" ? "فجوة البحث" : "Research gap", pr?.research_gap),
        item(lang === "ar" ? "أدلة موجودة" : "Existing evidence", pr?.existing_evidence),
      ];
      break;
    case "problem_purpose":
      inputData = [
        item(lang === "ar" ? "الفجوة" : "Gap", pr?.research_gap),
        item(lang === "ar" ? "الفكرة" : "Idea", pr?.refined_idea),
        pop,
      ];
      outputData = [
        item(lang === "ar" ? "مشكلة البحث" : "Research problem", pr?.research_problem),
        item(lang === "ar" ? "الهدف العام" : "Overall aim", pr?.overall_aim),
        item(
          lang === "ar" ? "الإسهام المتوقع" : "Expected contribution",
          pr?.expected_contribution
        ),
      ];
      break;
    case "questions_objectives":
      inputData = [
        item(lang === "ar" ? "المشكلة" : "Problem", pr?.research_problem),
        item(lang === "ar" ? "الهدف" : "Aim", pr?.overall_aim),
      ];
      outputData = [
        item(
          lang === "ar" ? "عدد الأسئلة" : "Questions count",
          String(questions.length)
        ),
        ...questions.slice(0, 3).map((q, i) =>
          item(
            lang === "ar" ? `سؤال ${i + 1}` : `Question ${i + 1}`,
            q.text
          )
        ),
        item(
          lang === "ar" ? "عدد الأهداف" : "Objectives count",
          String(objectives.length)
        ),
      ];
      break;
    case "hypotheses":
      inputData = [
        item(
          lang === "ar" ? "الأسئلة" : "Questions",
          questions.map((q) => q.text).join(" | ") || null
        ),
      ];
      outputData = [
        item(
          lang === "ar" ? "حالة المرحلة" : "Stage status",
          status
        ),
        item(
          lang === "ar" ? "ملاحظة" : "Note",
          lang === "ar"
            ? "أضف الفرضيات من لوحة البنية"
            : "Add hypotheses from Structure panel"
        ),
      ];
      break;
    case "constructs_variables":
      inputData = [
        item(
          lang === "ar" ? "الأسئلة" : "Questions",
          String(questions.length)
        ),
        item(lang === "ar" ? "المفاهيم" : "Concepts", pr?.key_concepts),
      ];
      outputData = [
        item(
          lang === "ar" ? "ملاحظة" : "Note",
          lang === "ar"
            ? "عرّف المتغيرات في لوحة البنية"
            : "Define variables in Structure panel"
        ),
      ];
      break;
    case "methodology":
      inputData = [
        item(
          lang === "ar" ? "نوع الأسئلة" : "Question types",
          [...new Set(questions.map((q) => q.question_type))].join(", ") || null
        ),
        docType,
      ];
      outputData = [
        item(
          lang === "ar" ? "ملاحظة" : "Note",
          lang === "ar"
            ? "سجّل التصميم في لوحة البنية"
            : "Record design in Structure panel"
        ),
      ];
      break;
    case "population_sampling":
      inputData = [pop, field, title];
      outputData = [
        item(lang === "ar" ? "ملخص المجتمع" : "Population summary", project.population_summary),
      ];
      break;
    case "instruments":
      inputData = [
        item(
          lang === "ar" ? "الأسئلة" : "Questions",
          String(questions.length)
        ),
        item(
          lang === "ar" ? "التحليل المقترح" : "Proposed analyses",
          questions.map((q) => q.proposed_analysis).filter(Boolean).join("; ") || null
        ),
      ];
      outputData = [
        item(
          lang === "ar" ? "ملاحظة" : "Note",
          lang === "ar"
            ? "أضف الأدوات من لوحة البنية"
            : "Add instruments from Structure panel"
        ),
      ];
      break;
    case "validity_quality":
      inputData = [
        item(
          lang === "ar" ? "حالة الأدوات" : "Instruments stage",
          "linked to Structure panel"
        ),
      ];
      outputData = [
        item(
          lang === "ar" ? "ملاحظة" : "Note",
          lang === "ar"
            ? "وثّق الصدق/الثبات بعد التجريب"
            : "Document validity/reliability after pilot"
        ),
      ];
      break;
    case "ethics":
      inputData = [
        item(
          lang === "ar" ? "متطلبات الأخلاقيات" : "Ethics requirements",
          pr?.ethics_requirements
        ),
        pop,
      ];
      outputData = [
        item(
          lang === "ar" ? "متطلبات الأخلاقيات" : "Ethics requirements",
          pr?.ethics_requirements
        ),
      ];
      break;
    case "analysis_plan":
      inputData = [
        ...questions.slice(0, 4).map((q, i) =>
          item(
            lang === "ar" ? `تحليل س${i + 1}` : `Analysis Q${i + 1}`,
            q.proposed_analysis || q.text
          )
        ),
      ];
      outputData = [
        item(
          lang === "ar" ? "خطط مرتبطة بالأسئلة" : "Plans linked to questions",
          String(questions.filter((q) => q.proposed_analysis).length)
        ),
      ];
      break;
    case "results":
    case "discussion":
    case "conclusion":
      inputData = [
        item(
          lang === "ar" ? "نسبة اكتمال المشروع" : "Project completion",
          `${project.completion_percent}%`
        ),
        item(
          lang === "ar" ? "المرحلة الحالية" : "Current stage",
          project.current_stage
        ),
      ];
      outputData = [
        item(
          lang === "ar" ? "حالة هذه المرحلة" : "This stage status",
          status
        ),
      ];
      break;
    case "abstract_title":
      inputData = [
        title,
        item(lang === "ar" ? "الهدف" : "Aim", pr?.overall_aim),
        item(lang === "ar" ? "المشكلة" : "Problem", pr?.research_problem),
      ];
      outputData = [title, field, docType];
      break;
    case "references":
      inputData = [
        item(
          lang === "ar" ? "مراجع محفوظة" : "Saved references",
          String(references.length)
        ),
        item(
          lang === "ar" ? "أسلوب التوثيق" : "Citation style",
          project.citation_style
        ),
      ];
      outputData = [
        ...references.slice(0, 4).map((r, i) =>
          item(
            lang === "ar" ? `مرجع ${i + 1}` : `Ref ${i + 1}`,
            r.title || r.authors || r.doi || `#${r.id}`
          )
        ),
      ];
      if (!references.length) {
        outputData = [
          item(
            lang === "ar" ? "قائمة المراجع" : "Reference list",
            lang === "ar" ? "لا مراجع بعد" : "No references yet"
          ),
        ];
      }
      break;
    default:
      inputData = [title, field];
      outputData = [
        item(lang === "ar" ? "الحالة" : "Status", status),
      ];
  }

  const filled =
    [...inputData, ...outputData].filter((d) => d.filled).length;
  const total = Math.max([...inputData, ...outputData].length, 1);
  const dataReady = Math.round((filled / total) * 100);
  // Blend data readiness with formal stage completion
  const readinessPercent = isComplete
    ? 100
    : status === "in_progress"
      ? Math.max(40, dataReady)
      : dataReady;

  return {
    stageKey,
    status,
    isCurrent,
    isComplete,
    completedAt: prog?.completed_at,
    guideInputs: guide?.inputs || "",
    guideProcessing: guide?.processing || guide?.how || "",
    guideOutputs: guide?.outputs || "",
    nextStageKey: guide?.nextStageKey || null,
    inputData,
    outputData,
    readinessPercent,
  };
}
