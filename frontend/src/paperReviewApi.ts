import { request } from "./api";
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
}
export interface PaperReview {
 id: number; project_id: number; filename: string; language: string; version: number;
 sections: ReviewSection[]; overview: ReviewFinding | null;
 analysis_mode: string; warnings: string[]; coverage_note: string; page_count: number;
 overview_truncated?: boolean;
 analysis_pending_ids?: number[];
}
export interface ReviewSummary { id: number; filename: string; language: string; analysis_mode: string }
const base = (project: number) => `/projects/${project}/paper-reviews`;
export const paperReviewApi = {
 list: (token:string,project:number) => request<ReviewSummary[]>(base(project),{},token),
 get: (token:string,project:number,id:number) => request<PaperReview>(`${base(project)}/${id}`,{},token),
 upload: (token:string,project:number,file:File,language:string) => { const form=new FormData(); form.append("file",file); return request<PaperReview>(`${base(project)}?language=${language}`,{method:"POST",body:form},token); },
 action: (token:string,project:number,review:PaperReview,path:string,data:object) => request<PaperReview>(`${base(project)}/${review.id}/${path}`,{method:"POST",body:JSON.stringify({version:review.version,...data})},token),
 save: (token:string,project:number,review:PaperReview,section:number,text:string) => request<PaperReview>(`${base(project)}/${review.id}/sections/${section}/draft`,{method:"PATCH",body:JSON.stringify({version:review.version,text})},token),
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
