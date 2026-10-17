/** Messages use application error codes only; never display an upstream response body. */
export function aiProviderFailure(text:string,c:(en:string,ar:string)=>string):string|null {
 const messages:[string,string,string][]=[
  ['AI_CREDIT_BALANCE','The AI provider’s API credit balance is exhausted. Ask the administrator to add API credits to the account linked to this task’s key, then retry. Application character ceilings do not affect this balance. Saved work is preserved.','نفد رصيد API لدى مزوّد الذكاء الاصطناعي. يجب على المسؤول شحن حساب API المرتبط بمفتاح هذه المهمة ثم إعادة المحاولة. رفع سقف أحرف البحث لا يعالج نفاد الرصيد. العمل المحفوظ باقٍ.'],
  ['AI_SPEND_LIMIT','The provider’s organization or project spending limit was reached. Ask the administrator to review that limit in the provider account before retrying. Saved work is preserved.','بلغ حساب المزوّد سقف الإنفاق للمؤسسة أو المشروع. اطلب من المسؤول مراجعة هذا السقف في حساب المزوّد قبل إعادة المحاولة. العمل المحفوظ باقٍ.'],
  ['AI_USAGE_LIMIT','The provider’s approved usage limit was reached. Ask the administrator to request a higher limit from the provider. Saved work is preserved.','بلغ الحساب حد الاستخدام المعتمد لدى المزوّد. يجب على المسؤول طلب زيادة الحد من المزوّد. العمل المحفوظ باقٍ.'],
  ['AI_QUOTA','The provider’s API quota is exhausted. Ask the administrator to check API credits, billing and usage limits for this task’s key before retrying. Saved work is preserved.','استُنفدت حصة API لدى المزوّد. اطلب من المسؤول التحقق من الرصيد والفوترة وحدود الاستخدام المرتبطة بمفتاح هذه المهمة قبل إعادة المحاولة. العمل المحفوظ باقٍ.'],
  ['AI_RATE_LIMIT','The provider’s request or token rate limit was reached. Wait before retrying. If it persists, send a shorter question or discuss a smaller section. Saved work is preserved.','تجاوز الطلب حد سرعة الطلبات أو الرموز لدى المزوّد. انتظر قبل إعادة المحاولة. إذا تكرر الخطأ، اختصر السؤال أو ناقش جزءاً أصغر من الورقة. العمل المحفوظ باقٍ.'],
 ];
 const match=messages.find(([code])=>text.includes(code+':'));
 return match?c(match[1],match[2]):null;
}
