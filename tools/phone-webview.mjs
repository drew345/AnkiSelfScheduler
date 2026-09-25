// Local USB-forwarded AnkiDroid WebView only. Never connects to other apps.
import fs from 'node:fs';
const pages=await (await fetch('http://127.0.0.1:9223/json')).json();
const page=pages.find(p=>p.url.includes('/deck-options/'));
if(!page) throw new Error('No Anki deck-options page');
const ws=new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
let expression=process.argv[2]==='--file'?fs.readFileSync(process.argv[3],'utf8'):process.argv[2];
if(process.argv[2]==='--install-scheduler'){
 const source=fs.readFileSync(new URL('../src/anki-custom-scheduler.js',import.meta.url),'utf8').replace(/\r\n/g,'\n');
 expression=`(()=>{const e=document.querySelector('textarea.card-state-customizer');if(!e||e.value)throw Error('Expected empty scheduling editor');e.value=${JSON.stringify(source)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return {matches:e.value===${JSON.stringify(source)},length:e.value.length};})()`;
}
if(process.argv[2]==='--verify-scheduler'){
 const source=fs.readFileSync(new URL('../src/anki-custom-scheduler.js',import.meta.url),'utf8').replace(/\r\n/g,'\n');
 expression=`document.querySelector('textarea.card-state-customizer')?.value===${JSON.stringify(source)}`;
}
const answer=new Promise((resolve,reject)=>{ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id===1)resolve(m);};ws.onerror=reject;});
ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression,returnByValue:true,awaitPromise:true}}));
const result=await answer;
console.log(JSON.stringify(result));
ws.close();
