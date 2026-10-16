// Server anchors use Unicode code-point offsets; textareas use UTF-16 offsets.
export function sourceAnchor(text:string,location:{start:number;end:number;quote:string}){
 const chars=Array.from(text);
 if(!Number.isInteger(location.start)||!Number.isInteger(location.end)||location.start<0||location.end<=location.start||location.end>chars.length)return null;
 const before=chars.slice(0,location.start).join('');const quote=chars.slice(location.start,location.end).join('');
 if(quote!==location.quote)return null;
 return {before,quote,after:chars.slice(location.end).join(''),selectionStart:before.length,selectionEnd:before.length+quote.length};
}
