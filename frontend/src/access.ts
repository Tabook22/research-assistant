export const pageGrants=[
 ['workspace','Research workspace','مساحة البحث'],
 ['create_projects','Create projects','إنشاء المشاريع'],
 ['paper_review','Full paper review & revision','تحليل الأوراق ومناقشتها وإعادة صياغتها'],
 ['paper_evaluate','Upload & evaluate papers only','رفع وتقييم الأوراق فقط'],
 ['research_desk','Research desk','مكتب البحث'],
 ['library','Paper library','مكتبة الأوراق'],
 ['documents','Uploaded documents','المستندات المرفوعة'],
 ['export','Project export page','صفحة تصدير المشروع'],
] as const;
export const panelPermission=(panel:string)=>['library','documents','export'].includes(panel)?panel:'workspace';
export function projectHome(id:number,can:(page:string)=>boolean){
 if(can('workspace'))return `/projects/${id}`;
 if(can('paper_review')||can('paper_evaluate'))return `/projects/${id}/review`;
 if(can('research_desk'))return `/projects/${id}/desk`;
 if(can('library'))return `/projects/${id}/library`;
 if(can('documents'))return `/projects/${id}/panel/documents`;
 if(can('export'))return `/projects/${id}/panel/export`;
 return '/account';
}
