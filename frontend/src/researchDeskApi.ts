import { request } from "./api";
export type TaskKind = "search" | "ask" | "compare" | "discover" | "write";
export interface Source { key:string; title:string; url:string; passages:number; reference_id?:number }
export interface Passage { id:number; source_key:string; title:string; location:string; source_url:string; text:string; fingerprint:string; evidence_id?:number }
export interface Citation { id:number; quote:string; source:Passage }
export interface Claim { text:string; interpretation:boolean; citations:Citation[] }
export interface DiscoveryItem { title:string; authors?:string; year?:number; doi?:string; url?:string; abstract?:string; journal?:string; open_access_url?:string; providers:string[]; coverage:string; reason:string }
export interface DeskResult { matches?:Passage[]; mode?:string; query_expansions?:string[]; warnings?:string[]; searched_sources?:number; claims?:Claim[]; limitations?:string[]; follow_up_questions?:string[]; coverage?:string; citation_check?:string; retrieval?:{mode:string;warnings:string[];searched_sources:number}; results?:DiscoveryItem[]; providers?:{provider:string;status:string;message?:string;count?:number}[]; coverage_note?:string }
export interface DeskJob { id:number; kind:TaskKind; status:string; message:string; payload:Record<string,unknown>; result:DeskResult|null; created_at:string }
export interface Evidence { id:number; claim:string; quote:string; source:Passage; notes:string; relationship:string; version:number }
export interface DeskDraft { id:number; title:string; text:string; evidence:Evidence[]; version:number; revisions:{text:string;title:string;saved_at:string}[] }
export interface Brief { content:string; version:number }
const base=(project:number)=>`/projects/${project}/desk`;
export const deskApi={
 linkReference:(t:string,p:number,source_key:string,reference_id:number)=>request(base(p)+"/source-reference",{method:"PUT",body:JSON.stringify({source_key,reference_id})},t),
 exportReferences:async(t:string,p:number)=>{const r=await fetch((import.meta.env.VITE_API_BASE||"/api")+base(p)+"/references/export",{headers:{Authorization:`Bearer ${t}`}});if(!r.ok)throw new Error("Could not export references.");return r.blob();},
 sourceFile:async(t:string,p:number,key:string)=>{const [kind,id]=key.split(":");const path=kind==="review"?`paper-reviews/${id}/file`:kind==="library"?`library/${id}/file`:`documents/${id}/file`;const r=await fetch((import.meta.env.VITE_API_BASE||"/api")+`/projects/${p}/${path}`,{headers:{Authorization:`Bearer ${t}`}});if(!r.ok){const body=await r.json().catch(()=>({}));throw new Error(body.detail||"Original file unavailable.");}return r.blob();},
 sources:(t:string,p:number)=>request<{sources:Source[];index:{passages:number;sources:number;updated_passages:number}}>(base(p)+"/sources",{},t),
 jobs:(t:string,p:number)=>request<DeskJob[]>(base(p)+"/jobs",{},t),
 job:(t:string,p:number,id:number)=>request<DeskJob>(base(p)+`/jobs/${id}`,{},t),
 start:(t:string,p:number,data:object)=>request<DeskJob>(base(p)+"/jobs",{method:"POST",body:JSON.stringify(data)},t),
 cancel:(t:string,p:number,id:number)=>request<DeskJob>(base(p)+`/jobs/${id}/cancel`,{method:"POST"},t),
 evidence:(t:string,p:number)=>request<Evidence[]>(base(p)+"/evidence",{},t),
 saveEvidence:(t:string,p:number,data:object)=>request<Evidence>(base(p)+"/evidence",{method:"POST",body:JSON.stringify(data)},t),
 editEvidence:(t:string,p:number,id:number,data:object)=>request<Evidence>(base(p)+`/evidence/${id}`,{method:"PATCH",body:JSON.stringify(data)},t),
 brief:(t:string,p:number)=>request<Brief>(base(p)+"/brief",{},t),
 saveBrief:(t:string,p:number,data:Brief)=>request<Brief>(base(p)+"/brief",{method:"PUT",body:JSON.stringify(data)},t),
 import:(t:string,p:number,job:number,index:number)=>request<{id:number;already_saved:boolean}>(base(p)+`/jobs/${job}/import/${index}`,{method:"POST"},t),
 checks:(t:string,p:number)=>request<Record<number,Record<string,unknown>>>(base(p)+"/reference-checks",{},t),
 verify:(t:string,p:number,id:number)=>request<Record<string,unknown>>(base(p)+`/references/${id}/verify`,{method:"POST"},t),
 drafts:(t:string,p:number)=>request<DeskDraft[]>(base(p)+"/drafts",{},t),
 keepDraft:(t:string,p:number,id:number)=>request<DeskDraft>(base(p)+`/jobs/${id}/draft`,{method:"POST"},t),
 editDraft:(t:string,p:number,d:DeskDraft)=>request<DeskDraft>(base(p)+`/drafts/${d.id}`,{method:"PATCH",body:JSON.stringify({version:d.version,title:d.title,text:d.text})},t),
 exportDraft:async(t:string,p:number,id:number,format:string)=>{const r=await fetch((import.meta.env.VITE_API_BASE||"/api")+base(p)+`/drafts/${id}/export?format=${format}`,{headers:{Authorization:`Bearer ${t}`}});if(!r.ok)throw new Error("Could not export the draft.");return r.blob();},
};
