import { request, sourceBlob } from "./api";
export interface ReviewFinding {
 summary: string; main_ideas: string[]; problem_statement: string;
 problem_status: "explicit" | "inferred" | "not_identified";
 strengths: string[]; improvements: string[]; evidence: string[]; verification_needed: string[];
}
export interface ReviewSection {
 id: number; title: string; page_start: number; page_end: number; original: string;
 draft: string | null; proposed_text?: string; analysis: ReviewFinding | null;
 revisions: {text: string; saved_at: string}[];
 messages: {role: string; content: string; created_at: string}[];
 annotations?: {items:PassageNote[];created_at:string};
}
export interface PassageNote {id:string;category:'strength'|'improvement'|'verification';severity:'low'|'medium'|'high';title:string;explanation:string;location:SourceLocation|null;replacement:string}
export interface PaperReview {
 presentation?: PaperPresentation;
 previous_presentation?: PaperPresentation;
 audience_questions?: AudienceQuestionSet;
 previous_audience_questions?: AudienceQuestionSet;
 rewrite_limits?: RewriteLimits;
 id: number; project_id: number; filename: string; language: string; version: number;
 sections: ReviewSection[]; overview: ReviewFinding | null;
 analysis_mode: string; warnings: string[]; coverage_note: string; page_count: number;
 overview_truncated?: boolean;
 analysis_pending_ids?: number[];
 source_format?: string;
 compliance?: ScientificReport;
 previous_compliance?: ScientificReport;
 rewrite?: WholePaperProposal;
 previous_rewrite?: WholePaperProposal;
 suggested_paper_type?: string;
 proposal_needs_input?: string[];
 origin_review_id?: number;
 paper_chat?: PaperChatHistory;
}
export type AudienceFormat='essay'|'multiple_choice'|'fill_blank'|'mixed';
export type SlideTheme='emerald'|'midnight'|'editorial';
export interface PaperSlide {id:number;title:string;focus:string;visual:'network'|'process'|'library'|'globe'|'science'|'balance';image_ready?:boolean;image_prompt_used?:string;image_style?:string;content:{bullets:string[];notes:string;image_prompt:string;location:SourceLocation;edited:boolean}|null}
export interface PaperPresentation {id:string;title:string;count:number;theme:SlideTheme;language:string;section_ids:number[];focus:string;created_at:string;updated_at:string;complete:boolean;stale:boolean;coverage:{mode:string;supplied_characters:number;total_characters:number};slides:PaperSlide[]}
export interface AudienceQuestion {id:number;format:Exclude<AudienceFormat,'mixed'>;topic:string;question:string;why_asked:string;answer:string;options:string[];correct_index:number|null;location:SourceLocation}
export interface AudienceQuestionSet {count:number;format:AudienceFormat;section_id:number|null;language:string;created_at:string;updated_at:string;complete:boolean;stale:boolean;coverage:{mode:string;supplied_characters:number;total_characters:number};questions:AudienceQuestion[]}
export interface PaperChatSession {id:string;number:number;title:string;created_at:string|null;updated_at:string|null;question_count:number;message_count:number;search_count:number;preview:string}
export interface RewriteLimits {scope:'global'|'project'|'review';target_id:number;mode:'inherit'|'custom'|'unlimited';source_limit:number|null;output_limit:number|null;discussion_limit:number|null}
export interface PaperChatHistory {messages:PaperChatMessage[];searches:PaperChatSearch[];sessions:PaperChatSession[];last_session_id?:string}
export interface AcademicChatSource {id:number;title:string;authors:string;year:number|null;doi:string;url:string|null;abstract:string;providers:string[];coverage:'abstract'|'metadata'}
export interface PaperChatSearch {id:string;session_id?:string;query:string;proposal_id:string;consented_at:string;created_at:string;results:AcademicChatSource[];providers:{provider:string;status:string;count?:number;message?:string}[]}
export interface PaperChatMessage {id:string;session_id?:string;role:'user'|'assistant';content:string;created_at:string;kind?:'search_results';search_id?:string;section_id?:number|null;locations?:SourceLocation[];unmatched_evidence?:number;follow_up_questions?:string[];external_sources?:AcademicChatSource[];coverage?:{mode:string;section_id:number|null;supplied_characters:number;total_characters:number};search_proposal?:{id:string;query:string;reason:string;used:boolean}}
export interface ProposedSection {id:number;title:string;purpose:string;source_section_ids:number[];result:{text:string;changes:string[];needs_input:string[]}|null}
export interface WholePaperProposal {source_snapshot?:{id:number;title:string;text:string}[];title:string;approach:string;problem_formulation:string;requirements_needing_input:string[];sections:ProposedSection[];paper_type:string;basis:'original'|'working';instruction:string;complete:boolean;stale?:boolean;copy_id?:number;created_at:string;updated_at:string}
export interface ReviewSummary { id: number; filename: string; language: string; analysis_mode: string }
export type CriterionStatus='met'|'partial'|'missing'|'unknown'|'not_applicable';
export interface SourceLocation {section_id:number;section_title:string;start:number;end:number;quote:string;basis:'original'|'working';page:number|null;page_start:number;page_end:number}
export interface ScientificCriterion {id:string;title_en:string;title_ar:string;description_en:string;description_ar:string;guidance_en:string;guidance_ar:string;source_id:string;conditional:boolean;result:{status:CriterionStatus;explanation:string;improvement:string;locations:SourceLocation[];target_section_id:number|null;validation_note:string}|null}
export interface ScientificReport {rubric_version:string;paper_type:string;basis:'original'|'working';fingerprint:string;created_at:string;updated_at:string;items:ScientificCriterion[];counts:Record<CriterionStatus|'pending',number>;complete:boolean;score:number|null;score_upper:number|null;assessment_coverage:number;applicable_count:number;verdict:string;stale?:boolean}
export interface ScientificCatalog {version:string;types:{id:string;en:string;ar:string}[];sources:{id:string;name:string;url:string;scope:string}[];reviewed_on:string;criteria:Record<string,ScientificCriterion[]>}
const base = (project: number) => `/projects/${project}/paper-reviews`;
export const paperReviewApi = {
 evaluationWorkspace:(token:string)=>request<{id:number}>('/paper-evaluation/workspace',{method:'POST'},token),
 catalog:(token:string,project:number)=>request<ScientificCatalog>(`${base(project)}/criteria/catalog`,{},token),
 originalFile:(token:string,project:number,id:number)=>sourceBlob(`${base(project)}/${id}/file`,token),
 list: (token:string,project:number) => request<ReviewSummary[]>(base(project),{},token),
 get: (token:string,project:number,id:number) => request<PaperReview>(`${base(project)}/${id}`,{},token),
 upload: (token:string,project:number,file:File,language:string) => { const form=new FormData(); form.append("file",file); return request<PaperReview>(`${base(project)}?language=${language}`,{method:"POST",body:form},token); },
 action: (token:string,project:number,review:PaperReview,path:string,data:object) => request<PaperReview>(`${base(project)}/${review.id}/${path}`,{method:"POST",body:JSON.stringify({version:review.version,...data})},token),
 save: (token:string,project:number,review:PaperReview,section:number,text:string) => request<PaperReview>(`${base(project)}/${review.id}/sections/${section}/draft`,{method:"PATCH",body:JSON.stringify({version:review.version,text})},token),
 renameChatSession:(token:string,project:number,review:PaperReview,id:string,title:string)=>request<PaperReview>(`${base(project)}/${review.id}/chat/sessions/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify({version:review.version,title})},token),
};

// Each response is persisted by the server before the next request starts.
// Retrying an incomplete review skips completed work, including its overview.
export async function analyzePaper(
 token:string, project:number, initial:PaperReview,
 progress:(review:PaperReview, label:string)=>void, stopped:()=>boolean,
) {
 let current=initial;
 const refresh=!!initial.overview && !initial.analysis_pending_ids?.length && initial.sections.every(s=>s.analysis!==null);
 const pending=initial.sections.filter(s=>refresh||!s.analysis||initial.analysis_pending_ids?.includes(s.id));
 if(!initial.overview||refresh) {
  progress(current,"overview");
  current=await paperReviewApi.action(token,project,current,"analyze?overview_only=true",{});
  progress(current,"");
 }
 for(const section of pending) {
  if(stopped())return current;
  progress(current,String(section.id));
  current=await paperReviewApi.action(token,project,current,`sections/${section.id}/analyze`,{});
  progress(current,"");
 }
 return current;
}

export async function reviewPassages(
 token:string,project:number,initial:PaperReview,
 progress:(review:PaperReview,section:string)=>void,stopped:()=>boolean,only?:number,
){
 let current=initial;
 const pending=initial.sections.filter(section=>only?section.id===only:!section.annotations);
 for(const section of pending){
  if(stopped())break;
  progress(current,section.title);
  current=await paperReviewApi.action(token,project,current,`sections/${section.id}/annotations`,{});
  progress(current,'');
 }
 return current;
}
