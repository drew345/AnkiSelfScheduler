"""Exercise custom JS against actual backend states in an isolated collection."""
import json
import math
import subprocess
import sys
from anki.collection import Collection
from google.protobuf.json_format import MessageToDict

c = Collection(sys.argv[1])
try:
    samples=[]
    for name in ['Kor2Eng5000','Eng2Kor5000','Burmese','Pocket Thai Vocab','Thai Alphabet','Thai Vowels and Vowel Combinations','Thai_Alphabet2']:
        did=c.decks.id(name,create=False)
        for typ in [0,1,2,3]:
            cid=c.db.scalar('select id from cards where did=? and type=? limit 1',did,typ)
            if cid:
                samples.append(dict(deck=name,type=typ,states=MessageToDict(c._backend.get_scheduling_states(cid),always_print_fields_with_no_presence=True)))
    script=c.get_config('cardStateCustomizer')
finally:c.close()
node=r'''
const fs=require('fs'), vm=require('vm');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
for (const s of input.samples) {
  const ctx={deckName:s.deck};
  vm.runInNewContext(input.script,{states:s.states,ctx});
}
process.stdout.write(JSON.stringify(input.samples));
'''
p=subprocess.run(['node','-e',node],input=json.dumps(dict(script=script,samples=samples)),text=True,capture_output=True,check=True)
results=json.loads(p.stdout)
for before,after in zip(samples,results):
    state=after['states']
    if before['deck'] not in ['Kor2Eng5000','Eng2Kor5000']:
        assert before==after,'non-Korean state changed'
    elif before['type'] in [0,1,3]:
        a=state['again']['normal'];h=state['hard']['normal']
        assert a.get('learning',a.get('relearning',{}).get('learning',{}))['scheduledSecs']==1500
        assert h.get('learning',h.get('relearning',{}).get('learning',{}))['scheduledSecs']==2400
        assert state['good']['normal']['review']['scheduledDays']==3
        assert state['easy']['normal']['review']['scheduledDays']==6
    else:
        x=max(2,float(before['states']['current']['normal']['review']['scheduledDays']))
        hard=min(3650,math.ceil(.8*x));good=min(3650,math.ceil(max(hard+1,1.8*x)));easy=min(3650,math.ceil(max(good+1,3*x)))
        assert [state[k]['normal']['review']['scheduledDays'] for k in ['hard','good','easy']]==[hard,good,easy]
print(json.dumps({'passed_samples':len(samples),'decks':sorted(set(s['deck'] for s in samples))}))
