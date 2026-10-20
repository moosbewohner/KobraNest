(()=>{
'use strict';
const catalog=KOBRIAN_TRANSLATIONS.en;
let language='de';try{language=localStorage.getItem('kobrian.assistant.language')==='en'?'en':'de';}catch{}
const texts=new WeakMap(),attributes=new WeakMap();
function translate(value){
 if(language!=='en')return value;
 const trimmed=value.trim();let rendered=catalog[trimmed];
 if(rendered===undefined){
  if(trimmed.startsWith('SSH verbunden · '))rendered=trimmed.replace('SSH verbunden · ','SSH connected · ');
  else if(/^Drucker · \d/.test(trimmed))rendered=trimmed.replace('Drucker · ','Printer · ');
  else if(trimmed.startsWith('Klipper-Status: '))rendered=trimmed.replace('Klipper-Status: ','Klipper status: ');
  else if(/^MCU-Tunnel \d$/.test(trimmed))rendered=trimmed.replace('MCU-Tunnel ','MCU tunnel ');
  else if(/^\d+ MiB frei; benötigt: mehr als 1562 MiB\.$/.test(trimmed))rendered=trimmed.replace(' MiB frei; benötigt: mehr als 1562 MiB.',' MiB free; required: more than 1562 MiB.');
  else if(trimmed.startsWith('Nur gelesen: '))rendered=trimmed.replace('Nur gelesen: ','Read-only: ').replace('. Es werden keine Dienste oder Druckaufträge verändert.','. No services or print jobs are changed.');
  else if(trimmed.startsWith('Prüfung fehlgeschlagen ('))rendered=trimmed.replace('Prüfung fehlgeschlagen (','Check failed (').replace('. Verbindung und Voraussetzungen prüfen.','. Check connection and prerequisites.');
  else if(trimmed.startsWith('Bestätigter Schritt: ')){const name=trimmed.slice(21).split('. Konsole')[0];rendered='Confirmed step: '+(catalog[name]||name)+'. Keep the console and assistant open until completion.';}
  else if(trimmed.startsWith('Passende Dienstdateien erzeugt: '))rendered=trimmed.replace('Passende Dienstdateien erzeugt: ','Matching service files generated: ').replace('. Anleitung: docs/PI.md.','. Instructions: docs/PI.md.');
 }
 return rendered===undefined?value:value.replace(trimmed,rendered);
}
function apply(){
 document.documentElement.lang=language;document.title=language==='en'?'Kobrian · Setup assistant':'Kobrian · Installationsassistent';
 const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 while(walker.nextNode()){
  const node=walker.currentNode;if(!node.parentElement||node.parentElement.closest('script,style,code,[data-language]'))continue;
  const record=texts.get(node),current=node.nodeValue;
  const source=record&&current===record.rendered?record.source:current;
  const rendered=translate(source);texts.set(node,{source,rendered});if(current!==rendered)node.nodeValue=rendered;
 }
 for(const element of document.querySelectorAll('[placeholder],[aria-label]')){
  const records=attributes.get(element)||{};
  for(const name of ['placeholder','aria-label'])if(element.hasAttribute(name)){
   const current=element.getAttribute(name),record=records[name];const source=record&&current===record.rendered?record.source:current;const rendered=translate(source);records[name]={source,rendered};if(current!==rendered)element.setAttribute(name,rendered);
  }attributes.set(element,records);
 }
 document.querySelectorAll('[data-language]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.language===language)));
}
document.querySelectorAll('[data-language]').forEach(button=>button.onclick=()=>{language=button.dataset.language;try{localStorage.setItem('kobrian.assistant.language',language);}catch{}apply();});
new MutationObserver(apply).observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['placeholder','aria-label']});
apply();
})();
