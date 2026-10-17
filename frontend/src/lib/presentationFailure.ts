import {aiProviderFailure} from './aiProviderFailure';
export function presentationFailure(text:string,c:(en:string,ar:string)=>string,hasSavedSlides:boolean):string {
 const provider=aiProviderFailure(text,c);if(provider)return provider;
 const messages:[string,string,string][]=[
  ['SLIDES_IMAGES_CONFIG','Ask the administrator to configure the Images profile. Illustrations and export remain available.','اطلب من المسؤول تهيئة إعداد صور العروض التقديمية. تبقى الرسوم التوضيحية وتصدير PowerPoint متاحين.'],
  ['AI_OUTPUT_LIMIT','The model exhausted its output budget. Ask the administrator to increase the analysis output token limit, then retry this step.','استهلك الموديل حد رموز الإجابة قبل إكمال الرد. اطلب من المسؤول زيادة حد إجابة موديل التحليل، ثم أعد هذه الخطوة.'],
  ['SLIDES_FORMAT','The model returned an invalid slide structure. Retry this step; the source paper was not changed.','أعاد الموديل بنية شرائح غير صالحة. أعد هذه الخطوة؛ لم يتغيّر نص الورقة.'],
  ['SLIDES_PLAN','The model returned a different slide count or an empty outline. Retry creating the outline.','أعاد الموديل عدد شرائح مختلفًا أو مخططًا فارغًا. أعد إنشاء المخطط.'],
  ['SLIDES_EVIDENCE','A source quotation did not match the paper. Continue to regenerate only the unfinished slide.','لم يتطابق اقتباس الشريحة مع نص الورقة. اضغط متابعة لإعادة توليد الشريحة غير المكتملة فقط.'],
  ['SLIDES_TEXT','The slide text exceeded the readable layout limit. Continue to regenerate this slide.','تجاوز نص الشريحة حدود التنسيق المقروء. اضغط متابعة لإعادة توليد هذه الشريحة.'],
  ['SLIDES_EMPTY','No extracted text is available in the selected scope. Choose a readable section or re-upload a searchable paper.','لا يوجد نص مستخرج في النطاق المختار. اختر جزءًا مقروءًا أو أعد رفع ورقة قابلة لاستخراج النص.'],
  ['SLIDES_SCOPE','One of the selected sections is no longer available. Reload the paper and choose the scope again.','أحد الأجزاء المختارة لم يعد متاحًا. أعد تحميل الورقة وحدد النطاق مجددًا.'],
  ['AI_TIMEOUT','The model timed out. Retry this step after a short wait.','انتهت مهلة رد الموديل. انتظر قليلًا ثم أعد هذه الخطوة.'],
  ['AI_CONNECTION','The server could not reach the model provider. Retry when the connection is restored.','تعذر اتصال الخادم بمزوّد الموديل. أعد المحاولة عند عودة الاتصال.'],
  ['AI_ACCESS','The provider rejected the API key or model access. Ask the administrator to check the analysis profile.','رفض المزوّد المفتاح أو صلاحية الموديل. اطلب من المسؤول التحقق من إعداد التحليل.'],
  ['AI_CONFIGURATION','The model rejected the request configuration. Ask the administrator to test the selected analysis model and its structured-output support.','رفض الموديل إعدادات الطلب. اطلب من المسؤول اختبار موديل التحليل ودعمه للمخرجات المنظمة.'],
  ['AI_REFUSAL','The provider declined this request. Review the requested scope and try a specific section.','امتنع المزوّد عن تنفيذ الطلب. راجع نطاقه وجرب جزءًا محددًا.'],
  ['AI_RESPONSE','The model response was empty, incomplete or unusable. Retry the unfinished step.','كانت استجابة الموديل فارغة أو غير مكتملة أو غير صالحة. أعد الخطوة غير المكتملة.'],
 ];
 let message=messages.find(([code])=>text.includes(code+':'));
 let result=message?c(message[1],message[2]):text.includes('SLIDES_STALE')||text.includes('changed')?c('The paper changed. Reload before continuing.','تغيّرت الورقة. أعد تحميلها قبل المتابعة.'):text.includes('not configured')?c('Ask the administrator to configure the analysis model.','اطلب من المسؤول تهيئة موديل التحليل.'):c('This step could not finish. Retry; if it persists, ask the administrator to check the server logs.','تعذر إكمال هذه الخطوة. أعد المحاولة؛ وإذا تكرر الخطأ، اطلب من المسؤول فحص سجلات الخادم.');
 return result+' '+(hasSavedSlides?c('Saved slides are preserved.','الشرائح المحفوظة باقية.'):c('No new presentation was saved.','لم يُحفظ عرض جديد.'));
}
